import subprocess
import time

# Try to restart LHM with WMI enabled via command line
# First check LHM command line args
print("=== LHM Command Line ===")
cmd = 'Get-CimInstance Win32_Process -Filter "ProcessId = 17768" | Select-Object CommandLine | ConvertTo-Csv -NoTypeInformation'
result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
print(result.stdout.strip())

# Check if OHM works
print("\n=== OpenHardwareMonitor WMI ===")
cmd2 = 'Get-CimInstance -Namespace "root\\OpenHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue | Select-Object Name, SensorType, Value | ConvertTo-Csv -NoTypeInformation'
result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd2], capture_output=True, text=True, timeout=5)
if result2.stdout.strip():
    print(result2.stdout.strip())
else:
    print("(empty)")

# Try starting LHM with /WMI flag
print("\n=== Trying to find LHM exe ===")
cmd3 = 'Get-Process -Name "LibreHardwareMonitor" -ErrorAction SilentlyContinue | Select-Object Path'
result3 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd3], capture_output=True, text=True, timeout=5)
print(result3.stdout.strip())
