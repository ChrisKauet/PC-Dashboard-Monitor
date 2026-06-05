import subprocess

# Test GPU Counter
print("=== GPU Usage Counter ===")
cmd_usage = (
    'Get-Counter "\\GPU Engine(*)\\Utilization Percentage" -ErrorAction SilentlyContinue '
    '| Select-Object -ExpandProperty CounterSamples '
    '| Where-Object { $_.CookedValue -gt 0 } '
    '| Measure-Object CookedValue -Sum '
    '| Select-Object -ExpandProperty Sum'
)
result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_usage], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result.stdout))
print("stderr:", repr(result.stderr))

# Test GPU Info
print("\n=== GPU Info ===")
cmd_info = 'Get-CimInstance Win32_VideoController | Select-Object -First 1 Name, AdapterRAM | ConvertTo-Csv -NoTypeInformation'
result2 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_info], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result2.stdout))

# Test LHM
print("\n=== LibreHardwareMonitor ===")
cmd_lhm = (
    'Get-CimInstance -Namespace "root\\LibreHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue '
    '| Select-Object Name, SensorType, Value | ConvertTo-Csv -NoTypeInformation'
)
result3 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_lhm], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result3.stdout[:500]) if result3.stdout.strip() else "(empty)")
print("stderr:", repr(result3.stderr[:200]) if result3.stderr.strip() else "(empty)")

# Test OpenHardwareMonitor
print("\n=== OpenHardwareMonitor ===")
cmd_ohm = (
    'Get-CimInstance -Namespace "root\\OpenHardwareMonitor" -ClassName "Sensor" -ErrorAction SilentlyContinue '
    '| Select-Object Name, SensorType, Value | ConvertTo-Csv -NoTypeInformation'
)
result4 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_ohm], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result4.stdout[:500]) if result4.stdout.strip() else "(empty)")
print("stderr:", repr(result4.stderr[:200]) if result4.stderr.strip() else "(empty)")

# Test WMI thermal zone
print("\n=== WMI Thermal Zone ===")
cmd_therm = (
    'Get-CimInstance -Namespace "root/wmi" -ClassName "MSAcpi_ThermalZoneTemperature" -ErrorAction SilentlyContinue '
    '| Select-Object -ExpandProperty CurrentTemperature'
)
result5 = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_therm], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result5.stdout))
print("stderr:", repr(result5.stderr[:200]) if result5.stderr.strip() else "(empty)")

# Test nvidia-smi
print("\n=== nvidia-smi ===")
result6 = subprocess.run(["powershell", "-NoProfile", "-Command", "nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --csv,noheader,nounits 2>&1"], capture_output=True, text=True, timeout=5)
print("stdout:", repr(result6.stdout))
print("stderr:", repr(result6.stderr[:200]) if result6.stderr.strip() else "(empty)")
