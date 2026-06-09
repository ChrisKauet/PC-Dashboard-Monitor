"""
PC Dashboard Monitor — Backend Collector
Reads local sensor data and pushes to Supabase every N seconds.
Also serves a local HTTP API for direct access.
"""

import os
import sys
import time
import json
import socket
import subprocess
import threading
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

import psutil

# ── Resolve .env relative to exe/script path ──────────────────────
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

# ── Load .env manually (no dependency) ────────────────────────────
def load_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PC Dashboard Monitor Backend")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run in background mode (no console output, for executable)"
    )
    return parser.parse_args()


load_env()

# ── Config ────────────────────────────────────────────────────────
PORT = int(os.getenv("SENSOR_PORT", 8080))
COOLDOWN = float(os.getenv("SENSOR_COOLDOWN", 5.0))
PUSH_INTERVAL = float(os.getenv("PUSH_INTERVAL", 5.0))

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # service_role key (backend only)

# ── Single-instance enforcement ───────────────────────────────────
def enforce_single_instance():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, "PCDashboardMonitor_SensorDash")
        last_error = kernel32.GetLastError()
        if last_error == 183:  # ERROR_ALREADY_EXISTS
            print("[SensorDash] Another instance is already running. Exiting.")
            sys.exit(0)
    except Exception:
        pass

enforce_single_instance()

# ── GPU Detection ─────────────────────────────────────────────────
NVIDIA_AVAILABLE = False
AMD_AVAILABLE = False

try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
    print("[INFO] nvidia-ml-py (pynvml) initialized")
except Exception:
    pass

try:
    import pyamdgpuinfo
    if pyamdgpuinfo.detect_gpus() > 0:
        AMD_AVAILABLE = True
        print("[INFO] pyamdgpuinfo initialized")
except Exception:
    pass

# ── Sensor: LibreHardwareMonitor CSV log reader (primary method) ─
_LHM_DIR = r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor"

def _find_latest_lhm_csv():
    """Encontra o CSV de log mais recente do LibreHardwareMonitor."""
    import glob
    pattern = os.path.join(_LHM_DIR, "LibreHardwareMonitorLog-*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def read_lhm_csv():
    """Lê temperatura de CPU e GPU do CSV de log do LHM.
    Retorna dict com cpu_temp e gpu_temp (float ou None).
    """
    csv_path = _find_latest_lhm_csv()
    if not csv_path:
        return {"cpu_temp": None, "gpu_temp": None}

    try:
        # Evitar ler arquivos muito antigos (> 60s = LHM parado)
        age = time.time() - os.path.getmtime(csv_path)
        if age > 60:
            return {"cpu_temp": None, "gpu_temp": None}

        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            # Ler apenas as 2 últimas linhas para evitar carregar arquivo inteiro
            lines = f.readlines()

        if len(lines) < 2:
            return {"cpu_temp": None, "gpu_temp": None}

        # Processar header — LHM usa os identificadores de sensor como colunas
        raw_headers = lines[0].rstrip("\n").split(",")
        headers = [h.strip().strip('"') for h in raw_headers]

        # Última linha de dados
        raw_values = lines[-1].rstrip("\n").split(",")
        values = [v.strip().strip('"') for v in raw_values]

        # Mapear header -> valor
        row = {}
        for i, h in enumerate(headers):
            if i < len(values):
                row[h] = values[i]

        cpu_temp = None
        gpu_temp = None

        # CPU: preferência por Tctl/Tdie (AMD) → temperature/2 do amdcpu → qualquer sensor cpu temp
        cpu_priority = [
            "/amdcpu/0/temperature/2",
            "/intelcpu/0/temperature/0",
            "/amdcpu/0/temperature/0",
            "/intelcpu/0/temperature/2",
        ]
        for key in cpu_priority:
            if key in row and row[key] not in ("", "NaN"):
                try:
                    v = float(row[key].replace(",", "."))
                    if 0 < v < 120:
                        cpu_temp = round(v, 1)
                        break
                except ValueError:
                    pass

        # Fallback CPU: qualquer coluna amdcpu ou intelcpu > temperature
        if cpu_temp is None:
            for k, v in row.items():
                if ("amdcpu" in k or "intelcpu" in k) and "temperature" in k and v not in ("", "NaN"):
                    try:
                        val = float(v.replace(",", "."))
                        if 0 < val < 120:
                            cpu_temp = round(val, 1)
                            break
                    except ValueError:
                        pass

        # GPU: AMD RX → /gpu-amd/0/temperature/0 (GPU Core), /gpu-amd/0/temperature/1 (Hot Spot)
        gpu_priority = [
            "/gpu-amd/0/temperature/0",
            "/gpu-nvidia/0/temperature/0",
            "/gpu-intel/0/temperature/0",
            "/gpu-amd/0/temperature/1",
        ]
        for key in gpu_priority:
            if key in row and row[key] not in ("", "NaN"):
                try:
                    v = float(row[key].replace(",", "."))
                    if 0 < v < 120:
                        gpu_temp = round(v, 1)
                        break
                except ValueError:
                    pass

        # Fallback GPU: qualquer coluna gpu-* > temperature
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

        return {"cpu_temp": cpu_temp, "gpu_temp": gpu_temp}

    except Exception as e:
        print(f"[LHM CSV] erro: {e}")
        return {"cpu_temp": None, "gpu_temp": None}


# ── Sensor: LibreHardwareMonitor / OpenHardwareMonitor via WMI ───
def read_lhm_sensors():
    sensors = []
    for namespace in ("root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"):
        try:
            cmd = (
                'Get-CimInstance -Namespace "' + namespace + '" -ClassName "Sensor" -ErrorAction SilentlyContinue'
                ' | Where-Object { $_.SensorType -eq "Temperature" }'
                ' | Select-Object Name, Value'
                ' | ConvertTo-Csv -NoTypeInformation'
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True, text=True, timeout=4,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().splitlines()
                if len(lines) >= 2:
                    for line in lines[1:]:
                        parts = line.replace('"', '').split(',')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            val_str = parts[1].strip().replace(',', '.')
                            try:
                                val = float(val_str)
                                sensors.append({"name": name, "value": val})
                            except ValueError:
                                pass
                    if sensors:
                        break
        except Exception:
            pass
    return sensors

# ── GPU: WMI fallback ────────────────────────────────────────────
def read_gpu_wmi():
    try:
        cmd_usage = (
            'Get-Counter "\\GPU Engine(*)\\Utilization Percentage" -ErrorAction SilentlyContinue'
            ' | Select-Object -ExpandProperty CounterSamples'
            ' | Where-Object { $_.CookedValue -gt 0 -and $_.Path -match "engtype_3d" }'
            ' | Measure-Object CookedValue -Average'
            ' | Select-Object -ExpandProperty Average'
        )
        result_usage = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd_usage],
            capture_output=True, text=True, timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        raw = result_usage.stdout.strip().replace(',', '.')
        gpu_usage = round(float(raw), 1) if raw else None

        cmd_info = (
            'Get-CimInstance Win32_VideoController'
            ' | Select-Object -First 1 Name, AdapterRAM'
            ' | ConvertTo-Csv -NoTypeInformation'
        )
        result_info = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd_info],
            capture_output=True, text=True, timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        vram_total = None
        gpu_vendor = None
        lines = result_info.stdout.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].replace('"', '').split(',')
            name = parts[0].strip() if parts[0] else ""
            vram_bytes = parts[1].strip() if len(parts) > 1 else ""
            try:
                vram_total = round(int(vram_bytes) / 1e6, 1)
            except Exception:
                vram_total = None
            name_lower = name.lower()
            if any(k in name_lower for k in ("nvidia", "geforce", "rtx", "gtx")):
                gpu_vendor = "nvidia"
            elif any(k in name_lower for k in ("amd", "radeon", "rx")):
                gpu_vendor = "amd"
            elif any(k in name_lower for k in ("intel", "arc", "iris")):
                gpu_vendor = "intel"
            else:
                gpu_vendor = "unknown"

        # Temperatura GPU via CSV do LHM (método principal)
        gpu_temp = read_lhm_csv().get("gpu_temp")

        # Fallback: WMI LHM sensors
        if gpu_temp is None:
            try:
                sensors = read_lhm_sensors()
                for s in sensors:
                    if "gpu" in s["name"].lower():
                        gpu_temp = s["value"]
                        break
            except Exception:
                pass

        return {
            "gpu_usage": round(gpu_usage, 1) if gpu_usage is not None else None,
            "gpu_temp": gpu_temp,
            "vram_used": None,
            "vram_total": vram_total,
            "gpu_fan_rpm": None,
            "gpu_vendor": gpu_vendor,
        }
    except Exception as e:
        print(f"[GPU WMI error] {e}")
        return dict(gpu_usage=None, gpu_temp=None, vram_used=None, vram_total=None, gpu_fan_rpm=None, gpu_vendor=None)

# ── GPU: Full read ───────────────────────────────────────────────
def read_gpu():
    if NVIDIA_AVAILABLE:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                "gpu_usage": float(utilization.gpu),
                "gpu_temp": float(temp),
                "vram_used": round(mem_info.used / 1e6, 1),
                "vram_total": round(mem_info.total / 1e6, 1),
                "gpu_fan_rpm": None,
                "gpu_vendor": "nvidia",
            }
        except Exception:
            pass

    if AMD_AVAILABLE:
        try:
            gpu = pyamdgpuinfo.get_gpu(0)
            return {
                "gpu_usage": round(gpu.query_load() * 100, 1),
                "gpu_temp": round(gpu.query_temperature(), 1),
                "vram_used": round(gpu.query_vram_usage() / 1e6, 1),
                "vram_total": round(gpu.memory_info["vram_size"] / 1e6, 1),
                "gpu_fan_rpm": None,
                "gpu_vendor": "amd",
            }
        except Exception:
            pass

    return read_gpu_wmi()

# ── CPU Temperature ──────────────────────────────────────────────
def read_cpu_temp():
    # Method 1: LHM CSV log (principal no Windows — não precisa de WMI habilitado)
    try:
        temp = read_lhm_csv().get("cpu_temp")
        if temp is not None:
            return temp
    except Exception:
        pass

    # Method 2: psutil (funciona no Linux com drivers de sensor)
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz", "zenpower"):
            if key in temps and temps[key]:
                return round(temps[key][0].current, 1)
    except Exception:
        pass

    # Method 3: LibreHardwareMonitor / OpenHardwareMonitor via WMI
    try:
        sensors = read_lhm_sensors()
        for s in sensors:
            if "cpu package" in s["name"].lower():
                return s["value"]
        for s in sensors:
            if "cpu" in s["name"].lower() and "temp" in s["name"].lower():
                return s["value"]
    except Exception:
        pass

    # Method 4: WMI MSAcpi_ThermalZoneTemperature
    try:
        cmd = (
            'Get-CimInstance -Namespace "root/wmi" -ClassName "MSAcpi_ThermalZoneTemperature" -ErrorAction SilentlyContinue'
            ' | Select-Object -ExpandProperty CurrentTemperature'
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout.strip().splitlines()[0].strip()
            kelvin_tenths = int(raw)
            celsius = round(kelvin_tenths / 10.0 - 273.15, 1)
            if -50 < celsius < 150:
                return celsius
    except Exception:
        pass

    return None

# ── Storage ──────────────────────────────────────────────────────
def read_storage():
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

# ── Collect all sensors ──────────────────────────────────────────
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

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("[Supabase] Client initialized")
        except Exception as e:
            print(f"[Supabase] Init error: {e}")
    return _supabase_client

def push_to_supabase(data):
    client = get_supabase_client()
    if not client:
        return

    try:
        record = {
            "cpu_usage": data.get("cpu_usage"),
            "cpu_temp": data.get("cpu_temp"),
            "cpu_cores": json.dumps(data.get("cpu_cores", [])),
            "gpu_usage": data.get("gpu_usage"),
            "gpu_temp": data.get("gpu_temp"),
            "vram_used": data.get("vram_used"),
            "vram_total": data.get("vram_total"),
            "gpu_fan_rpm": data.get("gpu_fan_rpm"),
            "ram_used": data.get("ram_used"),
            "ram_total": data.get("ram_total"),
            "ram_usage": data.get("ram_usage"),
            "storage": json.dumps(data.get("storage", [])),
            "uptime_sec": data.get("uptime_sec"),
            "hostname": data.get("hostname"),
            "gpu_vendor": data.get("gpu_vendor"),
        }
        client.table("sensor_readings").insert(record).execute()
    except Exception as e:
        print(f"[Supabase] Push error: {e}")

# ── Shared state ─────────────────────────────────────────────────
_latest_data = {"status": "initializing"}
_data_lock = threading.Lock()

def sensor_loop():
    global _latest_data
    while True:
        try:
            data = collect()
            data["status"] = "online"
            with _data_lock:
                _latest_data = data
            # Push to Supabase
            push_to_supabase(data)
        except Exception as e:
            with _data_lock:
                _latest_data = {"status": "error", "error": str(e)}
        time.sleep(COOLDOWN)

# ── HTTP Handler ─────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/sensors":
            with _data_lock:
                data = dict(_latest_data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

# ── Main ─────────────────────────────────────────────────────────
def main():
    args = parse_args()
    
    if not args.background:
        print(f"[SensorDash] Starting HTTP sensor collector on port {PORT}...")
        print(f"  NVIDIA: {NVIDIA_AVAILABLE} | AMD: {AMD_AVAILABLE}")
        print(f"  Cooldown: {COOLDOWN}s")
        print(f"  Supabase: {'enabled' if SUPABASE_URL else 'disabled'}")

    # Start sensor collection thread
    sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
    sensor_thread.start()

    if not args.background:
        # Start HTTP server (only in foreground mode)
        server = HTTPServer(("0.0.0.0", PORT), Handler)
        print(f"[SensorDash] Running at http://localhost:{PORT}/api/sensors")
        print(f"[SensorDash] Press Ctrl+C to stop.")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[SensorDash] Shutting down...")
            server.shutdown()
    else:
        # In background mode, just keep the thread alive
        try:
            while True:
                time.sleep(3600)  # Sleep in 1-hour chunks
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()