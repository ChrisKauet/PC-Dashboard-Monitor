import subprocess
import time
import os

lhm_path = r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor\LibreHardwareMonitor.exe"

if not os.path.exists(lhm_path):
    print(f"ERROR: LHM not found at {lhm_path}")
    exit(1)

print(f"Starting LHM from: {lhm_path}")

# Start LHM with WMI flag
proc = subprocess.Popen(
    [lhm_path, "/WMI"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
)

print(f"LHM started with PID: {proc.pid}")

# Wait for it to initialize
time.sleep(3)

# Check if running
check = subprocess.run(
    ["powershell", "-NoProfile", "-Command", "Get-Process -Name 'LibreHardwareMonitor' -ErrorAction SilentlyContinue | Select-Object ProcessName, Id"],
    capture_output=True, text=True, timeout=5
)
print(f"Process check: {check.stdout.strip()}")

# Wait more for WMI to register
time.sleep(3)

# Test WMI
cmd = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue | Where-Object { $_.SensorType -eq "Temperature" } | Select-Object Name, Value | ConvertTo-Csv -NoTypeInformation'
result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=10)
if result.stdout.strip():
    print(f"\n=== LHM Temperature Sensors ===\n{result.stdout.strip()}")
else:
    print("\n=== LHM WMI still empty ===")
    # Try Hardware class
    cmd2 = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Hardware" -ErrorAction SilentlyContinue | Select-Object Name | ConvertTo-Csv -NoTypeInformation'
    result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd2], capture_output=True, text=True, timeout=5)
    print(f"Hardware: {result2.stdout.strip()}")
