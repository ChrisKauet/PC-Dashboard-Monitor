# Imports
import time, socket, os, subprocess
from dotenv import load_dotenv
import psutil
from supabase import create_client

load_dotenv()

# Inicializar cliente Supabase com service_role key
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
INTERVAL = int(os.getenv("PUSH_INTERVAL_SECONDS", 5))

# ──────────────────────────────────────────
# Tentar nvidia-ml-py (pacote correto para NVIDIA)
# ──────────────────────────────────────────
NVIDIA_AVAILABLE = False
try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
    print("[INFO] nvidia-ml-py (pynvml) inicializado com sucesso")
except Exception as e:
    print(f"[AVISO] NVIDIA ML não disponível: {e}")

# ──────────────────────────────────────────
# Tentar pyamdgpuinfo (AMD)
# ──────────────────────────────────────────
AMD_AVAILABLE = False
try:
    import pyamdgpuinfo
    if pyamdgpuinfo.detect_gpus() > 0:
        AMD_AVAILABLE = True
        print("[INFO] pyamdgpuinfo inicializado com sucesso")
    else:
        print("[AVISO] pyamdgpuinfo carregado mas nenhuma GPU AMD detectada")
except Exception as e:
    print(f"[AVISO] pyamdgpuinfo não disponível: {e}")

# ──────────────────────────────────────────
# ──────────────────────────────────────────
# Auxiliar: Consultar sensores via LibreHardwareMonitor / OpenHardwareMonitor WMI
# ──────────────────────────────────────────
def read_lhm_sensors():
    """Lê sensores de temperatura do LibreHardwareMonitor ou OpenHardwareMonitor via WMI."""
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


# Fallback: WMI via PowerShell (Windows — qualquer vendor)
# Captura: GPU name, AdapterRAM, e uso via DXGI
# ──────────────────────────────────────────
def read_gpu_wmi():
    """Lê dados básicos de GPU via PowerShell WMI — funciona para qualquer vendor no Windows."""
    try:
        # Uso de GPU via counters de performance (GPU Engine)
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

        # Nome e VRAM via Win32_VideoController
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
                vram_total = round(int(vram_bytes) / 1e6, 1)  # bytes → MB
            except Exception:
                vram_total = None
            name_lower = name.lower()
            if "nvidia" in name_lower or "geforce" in name_lower or "rtx" in name_lower or "gtx" in name_lower:
                gpu_vendor = "nvidia"
            elif "amd" in name_lower or "radeon" in name_lower or "rx" in name_lower:
                gpu_vendor = "amd"
            elif "intel" in name_lower or "arc" in name_lower or "iris" in name_lower:
                gpu_vendor = "intel"
            else:
                gpu_vendor = "unknown"

        # Tentar obter temperatura de GPU via LibreHardwareMonitor
        gpu_temp = None
        try:
            sensors = read_lhm_sensors()
            for s in sensors:
                name_lower = s["name"].lower()
                if "gpu" in name_lower:
                    gpu_temp = s["value"]
                    break
        except Exception:
            pass

        return {
            "gpu_usage": round(gpu_usage, 1) if gpu_usage is not None else None,
            "gpu_temp": gpu_temp,
            "vram_used": None,  # DXGI não expõe memória usada sem DirectX
            "vram_total": vram_total,
            "gpu_fan_rpm": None,
            "gpu_vendor": gpu_vendor,
        }
    except Exception as e:
        print(f"[GPU WMI erro] {e}")
        return dict(gpu_usage=None, gpu_temp=None, vram_used=None, vram_total=None, gpu_fan_rpm=None, gpu_vendor=None)


def read_gpu():
    """Detecta GPU e retorna dados. Tenta NVIDIA ML → AMD → WMI (fallback universal)."""
    # ── NVIDIA via nvidia-ml-py ──
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
        except Exception as e:
            print(f"[GPU NVIDIA erro] {e}")

    # ── AMD via pyamdgpuinfo ──
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
        except Exception as e:
            print(f"[GPU AMD erro] {e}")

    # ── Fallback universal: WMI via PowerShell ──
    return read_gpu_wmi()


def read_cpu_temp():
    """Tenta ler temperatura do CPU. psutil.sensors_temperatures() no Linux, LHM/OHM no Windows."""
    # 1. Tentar psutil (comum no Linux)
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
            if key in temps and temps[key]:
                return round(temps[key][0].current, 1)
    except Exception:
        pass

    # 2. Tentar LibreHardwareMonitor / OpenHardwareMonitor no Windows via WMI
    try:
        sensors = read_lhm_sensors()
        # Procurar primeiro por "CPU Package" (temperatura geral do processador)
        for s in sensors:
            name_lower = s["name"].lower()
            if "cpu package" in name_lower:
                return s["value"]
        # Se não achar "CPU Package", pegar qualquer sensor contendo "cpu"
        for s in sensors:
            name_lower = s["name"].lower()
            if "cpu" in name_lower:
                return s["value"]
    except Exception:
        pass

    return None


def read_storage():
    discos = []
    for part in psutil.disk_partitions():
        if "cdrom" in part.opts or not part.fstype:
            continue
        try:
            u = psutil.disk_usage(part.mountpoint)
            discos.append({
                "label": part.device.replace("\\", ""),
                "used_gb": round(u.used / 1e9, 1),
                "total_gb": round(u.total / 1e9, 1),
                "usage_percent": u.percent,
            })
        except PermissionError:
            pass
    return discos


def collect():
    vm = psutil.virtual_memory()
    cores = psutil.cpu_percent(interval=0.3, percpu=True)
    gpu = read_gpu()

    return {
        "cpu_usage": round(psutil.cpu_percent(interval=0.3), 1),
        "cpu_temp": read_cpu_temp(),
        "cpu_cores": cores,
        "ram_used": round(vm.used / 1e9, 2),
        "ram_total": round(vm.total / 1e9, 2),
        "ram_usage": vm.percent,
        "storage": read_storage(),
        "uptime_sec": int(time.time() - psutil.boot_time()),
        "hostname": socket.gethostname(),
        **gpu,
    }


def main():
    print(f"[SensorDash] Iniciando. Enviando para Supabase a cada {INTERVAL}s...")
    print(f"  NVIDIA ML disponível : {NVIDIA_AVAILABLE}")
    print(f"  AMD disponível       : {AMD_AVAILABLE}")
    print(f"  Fallback WMI         : {'sim (PowerShell)' if not NVIDIA_AVAILABLE and not AMD_AVAILABLE else 'não necessário'}")
    while True:
        try:
            data = collect()
            supabase.table("sensor_readings").insert(data).execute()
            vendor = data.get("gpu_vendor") or "none"
            gpu_pct = data.get("gpu_usage")
            gpu_str = f"{gpu_pct}%" if gpu_pct is not None else "N/A"
            print(f"[OK] {data['hostname']} | CPU {data['cpu_usage']}% | GPU {gpu_str} ({vendor})")
        except Exception as e:
            print(f"[ERRO ao enviar] {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()