import subprocess
import time

# Wait longer - sometimes LHM takes time to populate WMI
print("Waiting 10 seconds for LHM to fully initialize...")
time.sleep(10)

# Test WMI again
cmd = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue | Where-Object { $_.SensorType -eq "Temperature" } | Select-Object Name, Value | ConvertTo-Csv -NoTypeInformation'
result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=10)
if result.stdout.strip():
    print(f"=== LHM Temperature Sensors ===\n{result.stdout.strip()}")
else:
    print("=== LHM WMI still empty after 10s ===")
    
    # Check if the namespace exists at all
    cmd2 = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "__NAMESPACE" -ErrorAction SilentlyContinue'
    result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd2], capture_output=True, text=True, timeout=5)
    print(f"Namespace check: {result2.stdout.strip()} | stderr: {result2.stderr.strip()}")
    
    # List all classes in the namespace
    cmd3 = 'Get-CimClass -Namespace "root\\LibreHardwareMonitor" -ErrorAction SilentlyContinue | Select-Object CimClassName'
    result3 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd3], capture_output=True, text=True, timeout=5)
    print(f"Classes: {result3.stdout.strip()}")
