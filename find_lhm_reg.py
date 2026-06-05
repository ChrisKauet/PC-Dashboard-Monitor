import subprocess, os, winreg

# Search all registry for LibreHardwareMonitor
print("=== Searching registry for LHM keys ===")

# Check common locations
locations = [
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\LibreHardwareMonitor"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\LibreHardwareMonitor"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\LibreHardwareMonitorNet"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\LibreHardwareMonitorNet"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\OpenHardwareMonitor"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\OpenHardwareMonitor"),
]

for hive, path in locations:
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        print(f"\n  FOUND: {path}")
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                print(f"    {name} = {value}")
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass

# Also check if LHM stores settings in a file
print("\n=== Checking for LHM settings files ===")
for root, dirs, files in os.walk(r"C:\Users\Kauezin"):
    for f in files:
        fl = f.lower()
        if "libre" in fl and (".json" in fl or ".xml" in fl or ".config" in fl or ".ini" in fl or ".cfg" in fl):
            print(f"  {os.path.join(root, f)}")
    # Don't recurse too deep
    depth = root.replace(r"C:\Users\Kauezin", "").count(os.sep)
    if depth > 4:
        dirs.clear()
