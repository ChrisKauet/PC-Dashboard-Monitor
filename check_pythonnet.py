import subprocess

# Check if pythonnet is available
result = subprocess.run(
    ["python", "-c", "import clr; print('pythonnet available')"],
    capture_output=True, text=True, timeout=5
)
print("pythonnet:", result.stdout.strip() or result.stderr.strip())

# Check if we can install it
result2 = subprocess.run(
    ["pip", "install", "pythonnet"],
    capture_output=True, text=True, timeout=30
)
print("pip install pythonnet:", result2.stdout[-200:] if result2.stdout else "")
print("pip install pythonnet stderr:", result2.stderr[-200:] if result2.stderr else "")
