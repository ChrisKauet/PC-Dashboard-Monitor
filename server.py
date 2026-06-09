"""
PC Dashboard Monitor — Backend Collector
Reads local sensor data and pushes to Supabase every N seconds.
Also serves a local HTTP API for direct access.
Supports --background flag for headless operation.
"""
import os
import sys
import time
import json
import socket
import subprocess
import threading

import psutil

# ── Argparse ──────────────────────────────────────────────────────
def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="PC Dashboard Monitor Backend")
    parser.add_argument("--background", action="store_true", help="Run in background mode (no console output)")
    return parser.parse_args()


# ── Load .env ─────────────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

def load_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

# ── Single-instance enforcement ───────────────────────────────────
def enforce_single_instance():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, "PCDashboardMonitor_SensorDash")
        last_error = kernel32.GetLastError()
        if last_error == 183:
            print("[SensorDash] Another instance already running. Exiting.")
            sys.exit(0)
    except Exception:
        pass

enforce_single_instance()

# ── Config ────────────────────────────────────────────────────────
COOLDOWN = 5.0

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# ── GPU Detection ─────────────────────────────────────────────────
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

# ── Sensor: LHM CSV ──────────────────────────────────────────────
_LHM_DIR = r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor"

def _find_latest_lhm_csv():
    import glob
    pattern = os.path.join(_LHM_DIR, "LibreHardwareMonitorLog-*.csv")
    files = glob.glob(pattern)
    return max(files, key=os.path.getmtime) if files else None

def read_lhm_csv():
    csv_path = _find_latest_lhm_csv()
    if not csv_path:
        return None
    try:
        age = time.time() - os.path.getmtime(csv_path)
        if age > 60:
            return None
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        if len(lines) < 2:
            return None
        raw_headers = lines[0].rstrip("\n").split(",")
        headers = [h.strip().strip('"') for h in raw_headers]
        raw_values = lines[-1].rstrip("\n").split(",")
        values = [v.strip().strip('"') for v in raw_values]
        row = {h: values[i] for i, h in enumerate(headers) if i < len(values)}

        def find_val(priority_keys):
            for key in priority_keys:
                if key in row and row[key] not in ("", "NaN"):
                    try:
                        v = float(row[key].replace(",", "."))
                        return round(v, 1)
                    except ValueError:
                        pass
            return None

        # CPU temperature
        cpu_temp = find_val([
            "/amdcpu/0/temperature/2",
            "/intelcpu/0/temperature/0",
            "/amdcpu/0/temperature/0",
            "/intelcpu/0/temperature/2",
        ])

        # GPU temperature (all vendors)
        gpu_temp = find_val([
            "/gpu-amd/0/temperature/0",     # AMD GPU Core
            "/gpu-amd/0/temperature/1",     # AMD GPU Hot Spot
            "/gpu-nvidia/0/temperature/0",  # NVIDIA
            "/gpu-intel/0/temperature/0",   # Intel Arc
        ])
        # Fallback: any gpu temperature sensor
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

        # GPU usage (AMD: Load, NVIDIA: GPU Load)
        gpu_usage = find_val([
            "/gpu-amd/0/load/0",            # AMD GPU Load %
            "/gpu-nvidia/0/load/0",         # NVIDIA GPU Load %
            "/gpu-intel/0/load/0",          # Intel GPU Load %
        ])
        if gpu_usage is not None:
            gpu_usage = max(0.0, min(100.0, gpu_usage))

        # VRAM: used/total in bytes
        vram_used_gb = None
        vram_total_gb = None
        vram_used_val = find_val([
            "/gpu-amd/0/smallData/0",       # AMD VRAM used (bytes)
            "/gpu-nvidia/0/smallData/0",    # NVIDIA VRAM used
        ])
        if vram_used_val is not None:
            vram_used_gb = round(vram_used_val / 1e9, 1)
        vram_total_val = find_val([
            "/gpu-amd/0/data/0",            # AMD VRAM total (bytes)
            "/gpu-nvidia/0/data/0",         # NVIDIA VRAM total
        ])
        if vram_total_val is not None:
            vram_total_gb = round(vram_total_val / 1e9, 1)

        # GPU Fan RPM
        gpu_fan_rpm = find_val([
            "/gpu-amd/0/fan/0",             # AMD GPU Fan
            "/gpu-nvidia/0/fan/0",          # NVIDIA GPU Fan
        ])

        # Detect GPU vendor from headers
        gpu_vendor = None
        gpu_headers = [h for h in headers if h.startswith("/gpu-")]
        if gpu_headers:
            first_gpu = gpu_headers[0]
            if "amd" in first_gpu:
                gpu_vendor = "amd"
            elif "nvidia" in first_gpu:
                gpu_vendor = "nvidia"
            elif "intel" in first_gpu:
                gpu_vendor = "intel"

        # CPU cores from LHM
        cpu_cores = None
        core_temps = []
        for h, v in row.items():
            if "temperature" in h and ("/amdcpu/" in h or "/intelcpu/" in h):
                try:
                    val = float(v.replace(",", "."))
                    if 0 < val < 120:
                        core_temps.append(val)
                except (ValueError, AttributeError):
                    pass

        return {
            "cpu_temp": cpu_temp,
            "gpu_temp": gpu_temp,
            "gpu_usage": gpu_usage,
            "vram_used": vram_used_gb,
            "vram_total": vram_total_gb,
            "gpu_fan_rpm": gpu_fan_rpm if gpu_fan_rpm and gpu_fan_rpm > 0 else None,
            "gpu_vendor": gpu_vendor,
            "lhm_stale": False,
        }
    except Exception as e:
        print(f"[LHM CSV] Error: {e}")
        return None

def read_cpu_temp():
    try:
        t = read_lhm_csv().get("cpu_temp")
        if t is not None:
            return t
    except Exception:
        pass
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz", "zenpower"):
            if key in temps and temps[key]:
                return round(temps[key][0].current, 1)
    except Exception:
        pass
    for ns in ("root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"):
        try:
            cmd = (f'Get-CimInstance -Namespace "{ns}" -ClassName "Sensor" '
                   '-ErrorAction SilentlyContinue | Where-Object { $_.SensorType -eq "Temperature" } '
                   '| Select-Object Name, Value')
            r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                               capture_output=True, text=True, timeout=4,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            if r.returncode == 0 and r.stdout.strip():
                for line in r.stdout.strip().splitlines():
                    low = line.lower()
                    if "cpu" in low and "temp" in low:
                        parts = line.split(",")
                        if len(parts) >= 2:
                            try:
                                return round(float(parts[1].strip().replace(",", ".")), 1)
                            except ValueError:
                                pass
                break
        except Exception:
            pass
    return None

def read_gpu():
    # Primary: LibreHardwareMonitor CSV
    lhm = read_lhm_csv()
    if lhm and (lhm.get("gpu_temp") is not None or lhm.get("gpu_usage") is not None):
        return {
            "gpu_usage": lhm.get("gpu_usage"),
            "gpu_temp": lhm.get("gpu_temp"),
            "vram_used": lhm.get("vram_used"),
            "vram_total": lhm.get("vram_total"),
            "gpu_fan_rpm": lhm.get("gpu_fan_rpm"),
            "gpu_vendor": lhm.get("gpu_vendor"),
        }

    # Fallback 1: pynvml (NVIDIA)
    if NVIDIA_AVAILABLE:
        try:
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            u = pynvml.nvmlDeviceGetUtilizationRates(h)
            t = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            m = pynvml.nvmlDeviceGetMemoryInfo(h)
            return {"gpu_usage": float(u.gpu), "gpu_temp": float(t),
                    "vram_used": round(m.used / 1e6, 1), "vram_total": round(m.total / 1e6, 1),
                    "gpu_fan_rpm": None, "gpu_vendor": "nvidia"}
        except Exception:
            pass

    # Fallback 2: pyamdgpuinfo (AMD)
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

    # Fallback 3: WMI (very limited)
    try:
        cmd = ('Get-Counter "\\GPU Engine(*)\\Utilization Percentage" -ErrorAction SilentlyContinue '
               '| Select-Object -ExpandProperty CounterSamples '
               '| Where-Object { $_.CookedValue -gt 0 -and $_.Path -match "engtype_3d" } '
               '| Measure-Object CookedValue -Average | Select-Object -ExpandProperty Average')
        r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                           capture_output=True, text=True, timeout=4,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        raw = r.stdout.strip().replace(",", ".")
        gpu_usage = round(float(raw), 1) if raw else None
        return {"gpu_usage": gpu_usage, "gpu_temp": None,
                "vram_used": None, "vram_total": None, "gpu_fan_rpm": None, "gpu_vendor": None}
    except Exception:
        pass

    return {"gpu_usage": None, "gpu_temp": None, "vram_used": None,
            "vram_total": None, "gpu_fan_rpm": None, "gpu_vendor": None}

def read_storage():
    disks = []
    for part in psutil.disk_partitions():
        if "cdrom" in part.opts or not part.fstype:
            continue
        try:
            u = psutil.disk_usage(part.mountpoint)
            disks.append({"label": part.device.replace("\\", ""),
                          "used_gb": round(u.used / 1e9, 1),
                          "total_gb": round(u.total / 1e9, 1),
                          "usage_percent": u.percent})
        except PermissionError:
            pass
    return disks

def collect():
    vm = psutil.virtual_memory()
    cores = psutil.cpu_percent(interval=0.3, percpu=True)
    gpu = read_gpu()
    return {
        "cpu_usage": round(psutil.cpu_percent(interval=0.3), 1),
        "cpu_temp": read_cpu_temp(),
        "cpu_cores": [round(c, 1) for c in cores],
        "ram_used": round(vm.used / 1e9, 2),
        "ram_total": round(vm.total / 1e9, 2),
        "ram_usage": vm.percent,
        "storage": read_storage(),
        "uptime_sec": int(time.time() - psutil.boot_time()),
        "hostname": socket.gethostname(),
        **gpu,
    }

# ── Supabase push ────────────────────────────────────────────────
_supabase_client = None

def push_to_supabase(data):
    global _supabase_client
    if SUPABASE_URL and SUPABASE_KEY and _supabase_client is None:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return
    if not _supabase_client:
        return
    try:
        record = {
            "cpu_usage": data.get("cpu_usage"), "cpu_temp": data.get("cpu_temp"),
            "cpu_cores": json.dumps(data.get("cpu_cores", [])),
            "gpu_usage": data.get("gpu_usage"), "gpu_temp": data.get("gpu_temp"),
            "vram_used": data.get("vram_used"), "vram_total": data.get("vram_total"),
            "gpu_fan_rpm": data.get("gpu_fan_rpm"),
            "ram_used": data.get("ram_used"), "ram_total": data.get("ram_total"),
            "ram_usage": data.get("ram_usage"),
            "storage": json.dumps(data.get("storage", [])),
            "uptime_sec": data.get("uptime_sec"), "hostname": data.get("hostname"),
            "gpu_vendor": data.get("gpu_vendor"),
        }
        _supabase_client.table("sensor_readings").insert(record).execute()
    except Exception:
        pass

# ── Sensor loop ──────────────────────────────────────────────────
_latest_data = {"status": "initializing"}
_data_lock = threading.Lock()
_running = True

def sensor_loop():
    global _latest_data
    while _running:
        try:
            data = collect()
            data["status"] = "online"
            with _data_lock:
                _latest_data = data
            push_to_supabase(data)
        except Exception as e:
            with _data_lock:
                _latest_data = {"status": "error", "error": str(e)}
        time.sleep(COOLDOWN)

# ── HTTP server ──────────────────────────────────────────────────
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/api/sensors", "/api/sensors/"):
            with _data_lock:
                data = dict(_latest_data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path in ("/health", "/health/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *_):
        pass

def http_server():
    port = PORT
    try:
        srv = HTTPServer(("0.0.0.0", port), Handler)
        print(f"[HTTP] Listening on port {port}")
        srv.serve_forever()
    except OSError as e:
        print(f"[HTTP] Cannot bind port {port}: {e}")

# ── Main ─────────────────────────────────────────────────────────
def main():
    global _running
    args = parse_args()

    if not args.background:
        print(f"[SensorDash] Starting on port {PORT}...")
        print(f"  NVIDIA: {NVIDIA_AVAILABLE} | AMD: {AMD_AVAILABLE}")
        print(f"  Cooldown: {COOLDOWN}s")
        print(f"  Supabase: {'enabled' if SUPABASE_URL and SUPABASE_KEY else 'disabled'}")

    threading.Thread(target=sensor_loop, daemon=True).start()
    threading.Thread(target=http_server, daemon=True).start()

    if args.background:
        try:
            while _running:
                time.sleep(1)
        except KeyboardInterrupt:
            _running = False
    else:
        print("[SensorDash] Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            _running = False


if __name__ == "__main__":
    main()
