import subprocess

# Check if LHM WMI provider is enabled
print("=== LHM WMI Provider Check ===")
cmd = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "__NAMESPACE" -ErrorAction SilentlyContinue | Select-Object Name'
result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result.stdout))
print("stderr:", repr(result.stderr))

# Check if LHM service/process is running
print("\n=== LHM Process Check ===")
cmd2 = 'Get-Process -Name "LibreHardwareMonitor" -ErrorAction SilentlyContinue | Select-Object ProcessName, Id'
result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd2], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result2.stdout))

# Try alternative: read from LHM HTTP API (if enabled)
print("\n=== LHM HTTP API (port 8085) ===")
try:
    import urllib.request
    req = urllib.request.urlopen("http://localhost:8085/data.json", timeout=3)
    data = req.read().decode()
    print(data[:500])
except Exception as e:
    print(f"Error: {e}")

# Try WMI with different class
print("\n=== WMI Hardware Check ===")
cmd3 = 'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Hardware" -ErrorAction SilentlyContinue | Select-Object Name, HardwareType | ConvertTo-Csv -NoTypeInformation'
result3 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd3], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result3.stdout[:500]))
print("stderr:", repr(result3.stderr[:200]))
