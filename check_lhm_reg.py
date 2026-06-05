import subprocess, os, winreg

# Check LHM registry settings
print("=== LHM Registry Settings ===")
try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\LibreHardwareMonitor", 0, winreg.KEY_READ)
    i = 0
    while True:
        try:
            name, value, _ = winreg.EnumValue(key, i)
            print(f"  {name} = {value}")
            i += 1
        except OSError:
            break
    winreg.CloseKey(key)
except FileNotFoundError:
    print("  (no registry key found)")

# Try to enable WMI via registry
print("\n=== Enabling WMI Provider via Registry ===")
try:
    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"SOFTWARE\LibreHardwareMonitor", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, "EnableWMI", 0, winreg.REG_DWORD, 1)
    winreg.CloseKey(key)
    print("  EnableWMI = 1 set in registry")
except Exception as e:
    print(f"  Error: {e}")

# Also check for the web server setting
print("\n=== Checking Web Server setting ===")
try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\LibreHardwareMonitor", 0, winreg.KEY_READ)
    i = 0
    while True:
        try:
            name, value, _ = winreg.EnumValue(key, i)
            if "web" in name.lower() or "http" in name.lower() or "server" in name.lower() or "port" in name.lower():
                print(f"  WEB: {name} = {value}")
            i += 1
        except OSError:
            break
    winreg.CloseKey(key)
except:
    pass
