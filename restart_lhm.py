import subprocess, time, os

lhm_path = r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor\LibreHardwareMonitor.exe"

# Kill existing LHM
print("Killing existing LHM process...")
subprocess.run(["powershell", "-NoProfile", "-Command", "Stop-Process -Name 'LibreHardwareMonitor' -Force -ErrorAction SilentlyContinue"], timeout=5)
time.sleep(2)

# Start LHM fresh
print(f"Starting LHM...")
proc = subprocess.Popen(
    [lhm_path],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
)
print(f"LHM started with PID: {proc.pid}")

# Wait for initialization
print("Waiting 8 seconds for LHM to initialize...")
time.sleep(8)

# Test WMI
cmd = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue | Where-Object { $_.SensorType -eq "Temperature" } | Select-Object Name, Value | ConvertTo-Csv -NoTypeInformation'
result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=10)
if result.stdout.strip():
    print(f"\n=== LHM Temperature Sensors ===\n{result.stdout.strip()}")
else:
    print("\n=== LHM WMI still empty ===")
    # List all classes
    cmd2 = 'Get-CimClass -Namespace "root\\LibreHardwareMonitor" -ErrorAction SilentlyContinue | Select-Object CimClassName'
    result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd2], capture_output=True, text=True, timeout=5)
    print(f"Classes: {result2.stdout.strip()}")
