import subprocess

# Check if OHM is installed
check = subprocess.run(
    ["powershell", "-NoProfile", "-Command", "Get-CimInstance -Namespace 'root\\OpenHardwareMonitor' -ClassName 'Sensor' -ErrorAction SilentlyContinue | Select-Object Name, SensorType, Value | ConvertTo-Csv -NoTypeInformation"],
    capture_output=True, text=True, timeout=5
)
print("OHM WMI:", check.stdout.strip() or "(empty)")

# Check LHM process with more detail
check2 = subprocess.run(
    ["powershell", "-NoProfile", "-Command", "Get-Process -Name 'LibreHardwareMonitor' -ErrorAction SilentlyContinue | Format-List ProcessName, Id, Path, MainWindowTitle"],
    capture_output=True, text=True, timeout=5
)
print("LHM Process:", check2.stdout.strip() or "(not running)")

# Check if there's an LHM HTTP server by trying to connect with a very short timeout
import socket
for port in [8085, 8080, 8081]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", port))
        print(f"Port {port} is OPEN!")
        s.close()
    except:
        print(f"Port {port} closed")
    finally:
        s.close()
