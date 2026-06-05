import subprocess, time, os, socket

lhm_path = r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor\LibreHardwareMonitor.exe"

# Kill any existing
subprocess.run(["powershell", "-NoProfile", "-Command", "Stop-Process -Name 'LibreHardwareMonitor' -Force -ErrorAction SilentlyContinue"], timeout=5)
time.sleep(1)

# Start LHM - the /WMI flag should enable WMI provider
print("Starting LHM with /WMI flag...")
proc = subprocess.Popen(
    [lhm_path, "/WMI"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.DETACHED_PROCESS
)
print(f"PID: {proc.pid}")

# Wait for it to fully initialize
for wait in [3, 5, 8, 12]:
    time.sleep(wait if wait == 3 else wait - (3 if wait == 5 else 5 if wait == 8 else 8))
    
    # Check if process is still running
    check = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Get-Process -Id {proc.pid} -ErrorAction SilentlyContinue | Select-Object ProcessName"],
        capture_output=True, text=True, timeout=3
    )
    if not check.stdout.strip():
        print(f"  t+{wait}s: Process died!")
        break
    
    # Test WMI
    cmd = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue | Where-Object { $_.SensorType -eq "Temperature" } | Select-Object Name, Value | ConvertTo-Csv -NoTypeInformation'
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
    
    if result.stdout.strip():
        print(f"  t+{wait}s: WMI WORKING!")
        print(result.stdout.strip())
        break
    else:
        # Check if namespace exists at all
        cmd2 = 'Get-CimClass -Namespace "root\\LibreHardwareMonitor" -ErrorAction SilentlyContinue | Select-Object -First 3 CimClassName'
        result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd2], capture_output=True, text=True, timeout=3)
        classes = result2.stdout.strip()
        print(f"  t+{wait}s: WMI empty. Classes: {classes or '(none)'}")
else:
    print("\n=== WMI never became available ===")
    print("The /WMI flag may not be supported in this version.")
    print("You need to enable WMI Provider in the LHM GUI: Options -> Enable WMI Provider")
