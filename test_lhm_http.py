import subprocess
import urllib.request
import json
import os

# Check LHM settings file
settings_paths = [
    os.path.join(os.environ.get("APPDATA", ""), "LibreHardwareMonitor", "settings.json"),
    r"C:\Users\Kauezin\AppData\Roaming\LibreHardwareMonitor\settings.json",
    r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor\LibreHardwareMonitor.exe.config",
]

for p in settings_paths:
    if os.path.exists(p):
        print(f"=== Settings found: {p} ===")
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        print(content[:1000])
    else:
        print(f"Not found: {p}")

# Try LHM HTTP API on common ports
for port in [8085, 8080, 8081, 8082, 8083, 8084]:
    try:
        req = urllib.request.urlopen(f"http://localhost:{port}/data.json", timeout=2)
        data = req.read().decode()
        print(f"\n=== LHM HTTP API on port {port} ===")
        print(data[:500])
        break
    except Exception:
        pass
else:
    print("\n=== LHM HTTP API not responding on any common port ===")

# Check if LHM has remote web server enabled
print("\n=== LHM Process Check ===")
result = subprocess.run(
    ["powershell", "-NoProfile", "-Command", "Get-Process -Name 'LibreHardwareMonitor' -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, Path"],
    capture_output=True, text=True, timeout=5
)
print(result.stdout.strip())
