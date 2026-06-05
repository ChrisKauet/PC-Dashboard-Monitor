import psutil
import subprocess
import json

print("=== psutil version:", psutil.__version__)
print("=== sensors_temperatures:", psutil.sensors_temperatures())

# Test LHM
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
            print(f"=== LHM ({namespace}):", result.stdout.strip())
    except Exception as e:
        print(f"=== LHM ({namespace}) error:", e)
