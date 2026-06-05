import subprocess, os, json

# Find and read all LHM config/settings files
search_dirs = [
    os.environ.get("APPDATA", ""),
    os.environ.get("LOCALAPPDATA", ""),
    r"C:\Users\Kauezin\Downloads\LibreHardwareMonitor",
]

for d in search_dirs:
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        fl = f.lower()
        if any(k in fl for k in ["setting", "config", "json", "xml"]):
            fp = os.path.join(d, f)
            print(f"\n=== {fp} ===")
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                    print(fh.read()[:500])
            except:
                print("(binary or unreadable)")
