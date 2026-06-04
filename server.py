"""
PC Dashboard Monitor — Backend Collector
No database. No Supabase. Pure Flask API serving real-time sensor data.
Single-instance enforcement. 1-second cooldown between readings.
"""

import os
import sys
import time
import socket
import subprocess
import threading
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

load_env()

# ── Config ────────────────────────────────────────────────────────
PORT = int(os.getenv("SENSOR_PORT", 8080))
COOLDOWN = float(os.getenv("SENSOR_COOLDOWN", 1.0))
TUNNEL_TYPE = os.getenv("TUNNEL_TYPE", "cloudflare")  # "cloudflare" or "ngrok"
TUNNEL_TOKEN = os.getenv("TUNNEL_TOKEN", "")
TUNNEL_URL_FILE = os.path.join(BASE_DIR, "tunnel_url.txt")

# ── Single-instance enforcement ───────────────────────────────────
def enforce_single_instance():
    """Use a named mutex to ensure only one instance runs."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, "PCDashboardMonitor_SensorDash")
        last_error = kernel32.GetLastError()
        if last_error == 183:  # ERROR_ALREADY_EXISTS
            print("[SensorDash] Another instance is already running. Exiting.")
            sys.exit(0)
    except Exception:
        pass  # Non-Windows or error — skip

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
                capture_output=True, text=True, timeout=4
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
        # GPU usage via performance counters
        cmd_usage = (
            'Get-Counter "\\GPU Engine(*)\\Utilization Percentage" -ErrorAction SilentlyContinue'
            ' | Select-Object -ExpandProperty CounterSamples'
            ' | Where-Object { $_.CookedValue -gt 0 }'
            ' | Measure-Object CookedValue -Sum'
            ' | Select-Object -ExpandProperty Sum'
        )
        result_usage = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd_usage],
            capture_output=True, text=True, timeout=4
        )
        raw = result_usage.stdout.strip().replace(',', '.')
        gpu_usage = min(float(raw), 100.0) if raw else None

        # GPU name + VRAM
        cmd_info = (
            'Get-CimInstance Win32_VideoController'
            ' | Select-Object -First 1 Name, AdapterRAM'
            ' | ConvertTo-Csv -NoTypeInformation'
        )
        result_info = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd_info],
            capture_output=True, text=True, timeout=4
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

        # GPU temp from LHM
        gpu_temp = None
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
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
            if key in temps and temps[key]:
                return round(temps[key][0].current, 1)
    except Exception:
        pass

    try:
        sensors = read_lhm_sensors()
        for s in sensors:
            if "cpu package" in s["name"].lower():
                return s["value"]
        for s in sensors:
            if "cpu" in s["name"].lower():
                return s["value"]
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

# ── Shared state (updated by background thread) ──────────────────
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
            import json
            self.wfile.write(json.dumps(data).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            import json
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs

# ── Tunnel: Cloudflare (preferred) or ngrok ─────────────────────
def start_tunnel():
    """Start a tunnel in a background thread and save the public URL."""
    if TUNNEL_TYPE == "cloudflare":
        start_cloudflare_tunnel()
    elif TUNNEL_TYPE == "ngrok":
        start_ngrok_tunnel()

def start_cloudflare_tunnel():
    try:
        # Check if cloudflared exists
        cloudflared_path = os.path.join(BASE_DIR, "cloudflared.exe")
        if not os.path.exists(cloudflared_path):
            # Try system PATH
            cloudflared_path = "cloudflared"

        cmd = [cloudflared_path, "tunnel", "--url", f"http://localhost:{PORT}"]
        if TUNNEL_TOKEN:
            cmd = [cloudflared_path, "tunnel", "run", "--token", TUNNEL_TOKEN]

        print(f"[Tunnel] Starting Cloudflare Tunnel...")
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )

        # Parse the tunnel URL from output
        for line in proc.stdout:
            line = line.strip()
            if "trycloudflare.com" in line or "cfargotunnel.com" in line:
                # Extract URL
                for word in line.split():
                    if word.startswith("https://") and ("trycloudflare.com" in word or "cfargotunnel.com" in word):
                        url = word.rstrip(".,;")
                        with open(TUNNEL_URL_FILE, "w") as f:
                            f.write(url)
                        print(f"[Tunnel] Public URL: {url}")
                        return
    except Exception as e:
        print(f"[Tunnel] Cloudflare failed: {e}")

def start_ngrok_tunnel():
    try:
        ngrok_path = os.path.join(BASE_DIR, "ngrok.exe")
        if not os.path.exists(ngrok_path):
            ngrok_path = "ngrok"

        cmd = [ngrok_path, "http", str(PORT)]
        if TUNNEL_TOKEN:
            cmd = [ngrok_path, "config", "add-authtoken", TUNNEL_TOKEN]
            subprocess.run(cmd, capture_output=True, timeout=10)
            cmd = [ngrok_path, "http", str(PORT)]

        print(f"[Tunnel] Starting ngrok...")
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )

        for line in proc.stdout:
            line = line.strip()
            if "ngrok-free.app" in line or "ngrok.io" in line:
                for word in line.split():
                    if word.startswith("https://") and "ngrok" in word:
                        url = word.rstrip(".,;")
                        with open(TUNNEL_URL_FILE, "w") as f:
                            f.write(url)
                        print(f"[Tunnel] Public URL: {url}")
                        return
    except Exception as e:
        print(f"[Tunnel] ngrok failed: {e}")

# ── Main ─────────────────────────────────────────────────────────
def main():
    print(f"[SensorDash] Starting HTTP sensor collector on port {PORT}...")
    print(f"  NVIDIA: {NVIDIA_AVAILABLE} | AMD: {AMD_AVAILABLE}")
    print(f"  Cooldown: {COOLDOWN}s")
    print(f"  Tunnel: {TUNNEL_TYPE}")

    # Start sensor collection thread
    sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
    sensor_thread.start()

    # Start tunnel thread
    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[SensorDash] Running at http://localhost:{PORT}/api/sensors")
    print(f"[SensorDash] Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SensorDash] Shutting down...")
        server.shutdown()

if __name__ == "__main__":
    main()
