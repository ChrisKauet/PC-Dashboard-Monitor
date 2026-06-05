import subprocess
import json

# Test LHM - all sensors
print("=== LibreHardwareMonitor - All Temperature Sensors ===")
cmd_lhm = (
    'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue '
    '| Where-Object { $_.SensorType -eq "Temperature" } '
    '| Select-Object Name, Value, Identifier '
    '| ConvertTo-Csv -NoTypeInformation'
)
result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_lhm], capture_output=True, text=True, timeout=5)
if result.stdout.strip():
    print(result.stdout.strip())
else:
    print("(empty)")

# Test LHM - all sensor types
print("\n=== LibreHardwareMonitor - All Sensor Types ===")
cmd_all = (
    'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue '
    '| Select-Object Name, SensorType, Value '
    '| ConvertTo-Csv -NoTypeInformation'
)
result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_all], capture_output=True, text=True, timeout=5)
if result2.stdout.strip():
    lines = result2.stdout.strip().splitlines()
    print(f"Total sensors: {len(lines) - 1}")
    for line in lines[:30]:
        print(line)
else:
    print("(empty)")

# Test GPU info again
print("\n=== GPU Info ===")
cmd_gpu = 'Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Csv -NoTypeInformation'
result3 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_gpu], capture_output=True, text=True, timeout=5)
print(result3.stdout.strip())
