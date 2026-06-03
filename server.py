# Imports
import time, socket, os
from dotenv import load_dotenv
import psutil
from supabase import create_client

load_dotenv()

# Inicializar cliente Supabase com service_role key
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
INTERVAL = int(os.getenv("PUSH_INTERVAL_SECONDS", 5))

# Tentar importar pyamdgpuinfo (AMD) e pynvml (NVIDIA)
AMD_AVAILABLE = False
NVIDIA_AVAILABLE = False
try:
    import pyamdgpuinfo
    AMD_AVAILABLE = True
except Exception:
    print("[AVISO] pyamdgpuinfo não disponível — dados de GPU AMD serão null")

try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
except Exception:
    print("[AVISO] pynvml não disponível — dados de GPU NVIDIA serão null")

def read_gpu():
    """Detecta GPU e retorna dados conforme vendor disponível"""
    # Prioridade: AMD primeiro, depois NVIDIA (ajustar se necessário)
    if AMD_AVAILABLE:
        try:
            gpu = pyamdgpuinfo.get_gpu(0)
            return {
                "gpu_usage": round(gpu.query_load() * 100, 1),
                "gpu_temp": round(gpu.query_temperature(), 1),
                "vram_used": round(gpu.query_vram_usage() / 1e6, 1),
                "vram_total": round(gpu.memory_info["vram_size"] / 1e6, 1),
                "gpu_fan_rpm": None,  # pyamdgpuinfo não fornece RPM diretamente
                "gpu_vendor": "amd"
            }
        except Exception as e:
            print(f"[GPU AMD erro] {e}")
            # continuar para tentar NVIDIA

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
                "gpu_fan_rpm": None,  # pynvml pode obter RPM mas requer permissão; deixaremos None por simplicidade
                "gpu_vendor": "nvidia"
            }
        except Exception as e:
            print(f"[GPU NVIDIA erro] {e}")
            # continuar para retornar None

    # Nenhuma GPU disponível ou erro
    return dict(gpu_usage=None, gpu_temp=None, vram_used=None, vram_total=None, gpu_fan_rpm=None, gpu_vendor=None)

def read_cpu_temp():
    # psutil.sensors_temperatures() não funciona no Windows nativamente.
    # Tentar chaves: 'coretemp', 'k10temp', 'cpu_thermal'
    # Se nenhuma disponível, retornar None.
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal"):
            if key in temps and temps[key]:
                return round(temps[key][0].current, 1)
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
    print(f"GPU AMD disponível: {AMD_AVAILABLE}")
    print(f"GPU NVIDIA disponível: {NVIDIA_AVAILABLE}")
    while True:
        try:
            data = collect()
            supabase.table("sensor_readings").insert(data).execute()
            vendor = data.get('gpu_vendor', 'none')
            print(f"[OK] {data['hostname']} | CPU {data['cpu_usage']}% | GPU {data['gpu_usage']}% ({vendor})")
        except Exception as e:
            print(f"[ERRO ao enviar] {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()