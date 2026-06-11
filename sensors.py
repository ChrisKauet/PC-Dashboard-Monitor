"""
Shared sensor collection library for PC Dashboard Monitor.
Pure sensor reading — no HTTP, no Supabase, no environment setup.
"""
import os
import time
import json
import glob
import socket
import subprocess
import logging
import urllib.request

import psutil

logger = logging.getLogger(__name__)

# ── GPU driver detection (at import time — no env dependency) ────
NVIDIA_AVAILABLE = False
AMD_AVAILABLE = False
try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
except Exception:
    pass
try:
    import pyamdgpuinfo
    if pyamdgpuinfo.detect_gpus() > 0:
        AMD_AVAILABLE = True
except Exception:
    pass


# ── LHM web server (port 8085) ───────────────────────────────────
_lhm_web_cache: dict = {}
_lhm_web_cache_time: float = 0.0
LHM_WEB_URL = "http://localhost:8085/data.json"
LHM_WEB_TTL = 4.0  # seconds to reuse cached response


def _parse_lhm_web(node: dict, result: dict) -> None:
    """Recursively walks LHM JSON tree extracting temperature/load values."""
    name = node.get("Text", "")
    value_str = node.get("Value", "")
    sensor_type = node.get("SensorType", "")

    if value_str and value_str not in ("-", ""):
        try:
            val = float(value_str.replace(",", ".").split(" ")[0])
        except ValueError:
            val = None
        if val is not None:
            lower_name = name.lower()
            parent_id = node.get("id", "")
            if sensor_type == "Temperature" or "°c" in value_str.lower() or "temp" in lower_name:
                if "cpu" in lower_name or "package" in lower_name or "tdie" in lower_name:
                    if result.get("cpu_temp") is None and 0 < val < 120:
                        result["cpu_temp"] = round(val, 1)
                elif "gpu" in lower_name and result.get("gpu_temp") is None and 0 < val < 120:
                    result["gpu_temp"] = round(val, 1)
            if sensor_type == "Load" or "%" in value_str:
                if ("gpu" in lower_name or "3d" in lower_name) and result.get("gpu_usage") is None and 0 <= val <= 100:
                    result["gpu_usage"] = round(val, 1)

    for child in node.get("Children", []):
        _parse_lhm_web(child, result)


def read_lhm_web() -> dict | None:
    """Query LHM's built-in HTTP server on port 8085. Returns parsed temps/loads."""
    global _lhm_web_cache, _lhm_web_cache_time
    now = time.time()
    if now - _lhm_web_cache_time < LHM_WEB_TTL and _lhm_web_cache:
        return _lhm_web_cache
    try:
        with urllib.request.urlopen(LHM_WEB_URL, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result: dict = {"cpu_temp": None, "gpu_temp": None, "gpu_usage": None}
        _parse_lhm_web(data, result)
        _lhm_web_cache = result
        _lhm_web_cache_time = now
        return result
    except Exception:
        return None


# ── Auto-launch LHM if not running ───────────────────────────────
_lhm_launch_attempted = False


def _restart_lhm_if_needed() -> None:
    """Kill running LHM (requires our process to be elevated) and relaunch with updated config."""
    try:
        import ctypes
        # Only attempt if we are elevated
        if not ctypes.windll.shell32.IsUserAnAdmin():
            return
        subprocess.run(
            ["taskkill", "/F", "/IM", "LibreHardwareMonitor.exe"],
            capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(1)
        _enable_lhm_web_server()
        lhm_dir = _get_lhm_dir()
        exe = os.path.join(lhm_dir, "LibreHardwareMonitor.exe")
        if os.path.isfile(exe):
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 2  # SW_SHOWMINIMIZED
            subprocess.Popen([exe], cwd=lhm_dir, startupinfo=si,
                             creationflags=subprocess.CREATE_NO_WINDOW)
            logger.info("[LHM] Restarted with updated config")
            time.sleep(5)
    except Exception as e:
        logger.debug("[LHM] Restart skipped: %s", e)


def _is_lhm_running() -> bool:
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq LibreHardwareMonitor.exe", "/NH"],
            capture_output=True, text=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return "LibreHardwareMonitor.exe" in r.stdout
    except Exception:
        return False


def _enable_lhm_web_server() -> None:
    """Patches LHM config to enable web server on port 8085 (idempotent)."""
    cfg = os.path.join(_get_lhm_dir(), "LibreHardwareMonitor.config")
    if not os.path.isfile(cfg):
        return
    try:
        with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if 'key="runWebServerMenuItem" value="false"' in content:
            content = content.replace(
                'key="runWebServerMenuItem" value="false"',
                'key="runWebServerMenuItem" value="true"',
            )
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("[LHM] Web server enabled in config")
    except Exception as e:
        logger.warning("[LHM] Could not patch config: %s", e)


def _register_lhm_task_scheduler() -> None:
    """
    Registers LHM in Windows Task Scheduler with highest privileges so it
    auto-starts at login without a UAC prompt on subsequent boots.
    One-time setup — skips if task already registered.
    """
    task_name = "LibreHardwareMonitorAutoStart"
    try:
        check = subprocess.run(
            ["schtasks", "/Query", "/TN", task_name],
            capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if check.returncode == 0:
            return  # already registered
    except Exception:
        return

    lhm_dir = _get_lhm_dir()
    exe = os.path.join(lhm_dir, "LibreHardwareMonitor.exe")
    if not os.path.isfile(exe):
        return
    try:
        xml = (
            '<?xml version="1.0"?>'
            '<Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
            '<Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers>'
            '<Principals><Principal id="Author">'
            '<LogonType>InteractiveToken</LogonType>'
            '<RunLevel>HighestAvailable</RunLevel>'
            '</Principal></Principals>'
            '<Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
            '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
            '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
            '<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>'
            '<Priority>7</Priority></Settings>'
            '<Actions>'
            f'<Exec><Command>{exe}</Command><WorkingDirectory>{lhm_dir}</WorkingDirectory></Exec>'
            '</Actions>'
            '</Task>'
        )
        xml_path = os.path.join(os.environ.get("TEMP", "."), "lhm_task.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml)
        r = subprocess.run(
            ["schtasks", "/Create", "/TN", task_name, "/XML", xml_path, "/F"],
            capture_output=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            logger.info("[LHM] Registered in Task Scheduler as '%s'", task_name)
        else:
            logger.warning("[LHM] schtasks failed: %s", r.stderr)
    except Exception as e:
        logger.warning("[LHM] Task Scheduler registration failed: %s", e)


def ensure_lhm_running() -> bool:
    """
    Ensures LibreHardwareMonitor is running with elevated privileges.
    - Enables web server in config (idempotent)
    - Registers in Task Scheduler for auto-start at login (idempotent)
    - Launches via Task Scheduler (elevated) or ShellExecute runas
    """
    global _lhm_launch_attempted

    if _is_lhm_running():
        # If web server not responding, restart LHM to apply config changes
        if read_lhm_web() is None:
            _restart_lhm_if_needed()
        return True

    if _lhm_launch_attempted:
        return False

    _lhm_launch_attempted = True
    lhm_dir = _get_lhm_dir()
    exe = os.path.join(lhm_dir, "LibreHardwareMonitor.exe")
    if not os.path.isfile(exe):
        logger.warning("[LHM] Executable not found at %s", exe)
        return False

    _enable_lhm_web_server()
    _register_lhm_task_scheduler()

    # Try to start via Task Scheduler (already elevated, no UAC prompt)
    task_name = "LibreHardwareMonitorAutoStart"
    try:
        r = subprocess.run(
            ["schtasks", "/Run", "/TN", task_name],
            capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            logger.info("[LHM] Started via Task Scheduler")
            time.sleep(5)
            return _is_lhm_running()
    except Exception:
        pass

    # Fallback: ShellExecute runas (shows UAC on first run)
    try:
        import ctypes
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, None, lhm_dir, 2  # SW_SHOWMINIMIZED
        )
        if ret > 32:
            logger.info("[LHM] Started via ShellExecute runas (elevated)")
            time.sleep(5)
            return _is_lhm_running()
    except Exception as e:
        logger.warning("[LHM] Failed to start: %s", e)

    return False


# ── LHM directory — resolved lazily so env vars are loaded first ─
def _get_lhm_dir() -> str:
    env = os.environ.get("LHM_DIR", "").strip()
    if env and os.path.isdir(env):
        return env
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "Downloads", "LibreHardwareMonitor"),
        os.path.join(home, "Desktop", "LibreHardwareMonitor"),
        os.path.join(home, "Documents", "LibreHardwareMonitor"),
        r"C:\Program Files\LibreHardwareMonitor",
        r"C:\LibreHardwareMonitor",
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return os.path.join(home, "Downloads", "LibreHardwareMonitor")


# ── LHM CSV reader with mtime cache ──────────────────────────────
_lhm_cache: dict = {}
_lhm_cache_mtime: float = 0.0


def _find_latest_lhm_csv():
    lhm_dir = _get_lhm_dir()
    pattern = os.path.join(lhm_dir, "LibreHardwareMonitorLog-*.csv")
    files = glob.glob(pattern)
    return max(files, key=os.path.getmtime) if files else None


def read_lhm_csv() -> dict | None:
    global _lhm_cache, _lhm_cache_mtime
    csv_path = _find_latest_lhm_csv()
    if not csv_path:
        return None
    try:
        mtime = os.path.getmtime(csv_path)
        if time.time() - mtime > 90:
            return None
        if mtime == _lhm_cache_mtime and _lhm_cache:
            return _lhm_cache
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        if len(lines) < 2:
            return None
        headers = [h.strip().strip('"') for h in lines[0].rstrip("\n").split(",")]
        values = [v.strip().strip('"') for v in lines[-1].rstrip("\n").split(",")]
        row = {h: values[i] for i, h in enumerate(headers) if i < len(values)}

        def find_val(keys):
            for key in keys:
                if key in row and row[key] not in ("", "NaN"):
                    try:
                        return round(float(row[key].replace(",", ".")), 1)
                    except ValueError:
                        pass
            return None

        cpu_temp = find_val([
            "/amdcpu/0/temperature/2", "/intelcpu/0/temperature/0",
            "/amdcpu/0/temperature/0", "/intelcpu/0/temperature/2",
        ])
        gpu_temp = find_val([
            "/gpu-amd/0/temperature/0", "/gpu-amd/0/temperature/1",
            "/gpu-nvidia/0/temperature/0", "/gpu-intel/0/temperature/0",
        ])
        if gpu_temp is None:
            for k, v in row.items():
                if k.startswith("/gpu-") and "temperature" in k and v not in ("", "NaN"):
                    try:
                        val = float(v.replace(",", "."))
                        if 0 < val < 120:
                            gpu_temp = round(val, 1)
                            break
                    except ValueError:
                        pass

        gpu_usage = find_val([
            "/gpu-amd/0/load/0", "/gpu-nvidia/0/load/0", "/gpu-intel/0/load/0",
        ])
        if gpu_usage is not None:
            gpu_usage = max(0.0, min(100.0, gpu_usage))

        vram_used_val = find_val(["/gpu-amd/0/smallData/0", "/gpu-nvidia/0/smallData/0"])
        vram_total_val = find_val(["/gpu-amd/0/data/0", "/gpu-nvidia/0/data/0"])
        gpu_fan_rpm = find_val(["/gpu-amd/0/fan/0", "/gpu-nvidia/0/fan/0"])

        gpu_vendor = None
        gpu_headers = [h for h in headers if h.startswith("/gpu-")]
        if gpu_headers:
            first = gpu_headers[0]
            if "amd" in first:
                gpu_vendor = "amd"
            elif "nvidia" in first:
                gpu_vendor = "nvidia"
            elif "intel" in first:
                gpu_vendor = "intel"

        result = {
            "cpu_temp": cpu_temp,
            "gpu_temp": gpu_temp,
            "gpu_usage": gpu_usage,
            "vram_used": round(vram_used_val / 1e9, 1) if vram_used_val else None,
            "vram_total": round(vram_total_val / 1e9, 1) if vram_total_val else None,
            "gpu_fan_rpm": gpu_fan_rpm if gpu_fan_rpm and gpu_fan_rpm > 0 else None,
            "gpu_vendor": gpu_vendor,
        }
        _lhm_cache = result
        _lhm_cache_mtime = mtime
        return result
    except Exception as e:
        logger.warning("[LHM CSV] Parse error: %s", e)
        return None


# ── CPU temperature ───────────────────────────────────────────────
def _read_cpu_temp_wmi_acpi() -> float | None:
    """Windows ACPI thermal zones — works without LHM on most consumer boards."""
    try:
        import wmi  # type: ignore
        w = wmi.WMI(namespace="root\\wmi")
        temps = [
            t.CurrentTemperature / 10.0 - 273.15
            for t in w.MSAcpi_ThermalZoneTemperature()
        ]
        valid = [t for t in temps if 0 < t < 120]
        if valid:
            return round(max(valid), 1)
    except Exception:
        pass
    return None


def _read_cpu_temp_powershell_acpi() -> float | None:
    """Fallback: parse thermal zones via PowerShell — no Python wmi dep required."""
    try:
        cmd = (
            'Get-CimInstance -Namespace root\\wmi -ClassName MSAcpi_ThermalZoneTemperature '
            '-ErrorAction SilentlyContinue | Select-Object -ExpandProperty CurrentTemperature'
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0 and r.stdout.strip():
            vals = []
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if line.isdigit() or (line.replace(".", "").isdigit()):
                    t = float(line) / 10.0 - 273.15
                    if 0 < t < 120:
                        vals.append(t)
            if vals:
                return round(max(vals), 1)
    except Exception:
        pass
    return None


def read_cpu_temp() -> float | None:
    lhm = read_lhm_csv()
    if lhm and lhm.get("cpu_temp") is not None:
        return lhm["cpu_temp"]
    # WMI ACPI — nativo no Windows, sem dependência externa
    t = _read_cpu_temp_wmi_acpi()
    if t is not None:
        return t
    t = _read_cpu_temp_powershell_acpi()
    if t is not None:
        return t
    # psutil (Linux/Mac fallback — geralmente None no Windows)
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz", "zenpower"):
            if key in temps and temps[key]:
                return round(temps[key][0].current, 1)
    except Exception:
        pass
    return None


# ── GPU ───────────────────────────────────────────────────────────
def read_gpu(lhm: dict | None = None) -> dict:
    if lhm is None:
        lhm = read_lhm_csv()
    _empty = {"gpu_usage": None, "gpu_temp": None, "vram_used": None,
               "vram_total": None, "gpu_fan_rpm": None, "gpu_vendor": None}

    # pynvml — temperatura + uso + VRAM (NVIDIA, sem LHM)
    if NVIDIA_AVAILABLE:
        try:
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            u = pynvml.nvmlDeviceGetUtilizationRates(h)
            t = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            m = pynvml.nvmlDeviceGetMemoryInfo(h)
            try:
                fan = pynvml.nvmlDeviceGetFanSpeed(h)
            except Exception:
                fan = None
            return {
                "gpu_usage": float(u.gpu),
                "gpu_temp": float(t),
                "vram_used": round(m.used / 1e6, 1),
                "vram_total": round(m.total / 1e6, 1),
                "gpu_fan_rpm": fan,
                "gpu_vendor": "nvidia",
            }
        except Exception:
            pass

    # Windows GPU Engine counter — AMD/Intel usage (sem LHM)
    gpu_usage_wmi = None
    try:
        cmd = ('Get-Counter "\\GPU Engine(*)\\Utilization Percentage" -ErrorAction SilentlyContinue '
               '| Select-Object -ExpandProperty CounterSamples '
               '| Where-Object { $_.CookedValue -gt 0 -and $_.Path -match "engtype_3D" } '
               '| Measure-Object CookedValue -Sum | Select-Object -ExpandProperty Sum')
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        raw = r.stdout.strip().replace(",", ".")
        if raw:
            gpu_usage_wmi = round(float(raw), 1)
    except Exception:
        pass

    # Temperatura AMD via WMI (Win32_PerfFormattedData_GPUPerformanceCounters)
    gpu_temp_wmi = None
    try:
        cmd = (
            'Get-CimInstance -Namespace root\\cimv2 -ClassName Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine '
            '-ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty TemperatureF'
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        raw = r.stdout.strip()
        if raw and raw.replace(".", "").isdigit():
            f_val = float(raw)
            c_val = (f_val - 32) * 5 / 9
            if 0 < c_val < 120:
                gpu_temp_wmi = round(c_val, 1)
    except Exception:
        pass

    if gpu_usage_wmi is not None:
        return {
            "gpu_usage": gpu_usage_wmi,
            "gpu_temp": gpu_temp_wmi or (lhm.get("gpu_temp") if lhm else None),
            "vram_used": lhm.get("vram_used") if lhm else None,
            "vram_total": lhm.get("vram_total") if lhm else None,
            "gpu_fan_rpm": lhm.get("gpu_fan_rpm") if lhm else None,
            "gpu_vendor": lhm.get("gpu_vendor") if lhm else "amd",
        }

    if AMD_AVAILABLE:
        try:
            g = pyamdgpuinfo.get_gpu(0)
            return {"gpu_usage": round(g.query_load() * 100, 1),
                    "gpu_temp": round(g.query_temperature(), 1),
                    "vram_used": round(g.query_vram_usage() / 1e6, 1),
                    "vram_total": round(g.memory_info["vram_size"] / 1e6, 1),
                    "gpu_fan_rpm": None, "gpu_vendor": "amd"}
        except Exception:
            pass

    if lhm and (lhm.get("gpu_temp") is not None or lhm.get("gpu_usage") is not None):
        return {k: lhm.get(k) for k in _empty}
    return _empty


# ── Storage ───────────────────────────────────────────────────────
def read_storage() -> list:
    disks = []
    for part in psutil.disk_partitions():
        if "cdrom" in part.opts or not part.fstype:
            continue
        try:
            u = psutil.disk_usage(part.mountpoint)
            disks.append({
                "label": part.device.replace("\\", ""),
                "used_gb": round(u.used / 1e9, 1),
                "total_gb": round(u.total / 1e9, 1),
                "usage_percent": u.percent,
            })
        except PermissionError:
            pass
    return disks


# ── Network speed ─────────────────────────────────────────────────
_prev_net_io = None
_prev_net_time: float = 0.0


def read_net_speed() -> tuple:
    """Returns (dl_mbps, ul_mbps) since last call. First call returns (None, None)."""
    global _prev_net_io, _prev_net_time
    try:
        io = psutil.net_io_counters()
        now = time.time()
        if _prev_net_io is not None:
            dt = now - _prev_net_time
            if dt > 0:
                dl = round((io.bytes_recv - _prev_net_io.bytes_recv) / dt / 1e6, 2)
                ul = round((io.bytes_sent - _prev_net_io.bytes_sent) / dt / 1e6, 2)
                _prev_net_io = io
                _prev_net_time = now
                return max(0.0, dl), max(0.0, ul)
        _prev_net_io = io
        _prev_net_time = now
    except Exception:
        pass
    return None, None


# ── Process list ──────────────────────────────────────────────────
def read_processes() -> list:
    """Returns top 10 processes sorted by CPU usage."""
    procs = []
    try:
        for p in psutil.process_iter(["name", "cpu_percent", "memory_info"]):
            try:
                info = p.info
                mem = info.get("memory_info")
                procs.append({
                    "name": info.get("name") or "unknown",
                    "cpu_percent": round(info.get("cpu_percent") or 0.0, 1),
                    "mem_mb": round((mem.rss if mem else 0) / 1e6, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass
    return sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:10]


# ── Full data collection ──────────────────────────────────────────
def collect() -> dict:
    vm = psutil.virtual_memory()
    cores = psutil.cpu_percent(interval=0.1, percpu=True)
    cpu_avg = round(sum(cores) / len(cores), 1) if cores else 0.0
    ensure_lhm_running()
    lhm_web = read_lhm_web()
    lhm = lhm_web or read_lhm_csv()
    gpu = read_gpu(lhm=lhm)
    cpu_temp = (lhm.get("cpu_temp") if lhm else None) or read_cpu_temp()
    dl_speed, ul_speed = read_net_speed()
    try:
        process_count = len(psutil.pids())
    except Exception:
        process_count = None
    return {
        "cpu_usage": cpu_avg,
        "cpu_temp": cpu_temp,
        "cpu_cores": [round(c, 1) for c in cores],
        "ram_used": round(vm.used / 1e9, 2),
        "ram_total": round(vm.total / 1e9, 2),
        "ram_usage": vm.percent,
        "storage": read_storage(),
        "uptime_sec": int(time.time() - psutil.boot_time()),
        "hostname": socket.gethostname(),
        "dl_speed": dl_speed,
        "ul_speed": ul_speed,
        "process_count": process_count,
        "processes": read_processes(),
        **gpu,
    }
