import clr
import os

# Add LHM lib path
lhm_dir = r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor"
clr.AddReference(os.path.join(lhm_dir, "LibreHardwareMonitorLib"))

from LibreHardwareMonitor.Hardware import Computer, HardwareType, SensorType

print("LibreHardwareMonitorLib loaded successfully!")

# Create computer instance
computer = Computer()
computer.IsCpuEnabled = True
computer.IsGpuEnabled = True
computer.IsMemoryEnabled = True
computer.IsMotherboardEnabled = True
computer.IsStorageEnabled = True
computer.Open()

print(f"\n=== Hardware detected ===")
for hardware in computer.Hardware:
    print(f"  [{hardware.HardwareType}] {hardware.Name}")
    hardware.Update()
    for sensor in hardware.Sensors:
        if sensor.SensorType == SensorType.Temperature:
            print(f"    🌡️  {sensor.Name}: {sensor.Value}°C")
        elif sensor.SensorType == SensorType.Load and "GPU" in str(sensor.Hardware.HardwareType):
            print(f"    📊 {sensor.Name}: {sensor.Value}%")

computer.Close()
print("\nDone!")
