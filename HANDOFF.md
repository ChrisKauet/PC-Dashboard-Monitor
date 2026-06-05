# PC Dashboard Monitor — Context Handoff
## Generated: 2026-06-04

## Project Location
`F:\VibeCoding\PC-Dashboard-Monitor`

## Stack
- **Backend:** Python (`server.py`) — collects sensor data, pushes to Supabase, serves HTTP API on port 8080
- **Frontend:** Next.js 16 (`dashboard/`) — fetches from `/api/sensors` (Supabase proxy route)
- **Database:** Supabase (project: `kcmdojajpdetksedzveu`)
- **Frontend Host:** Vercel (`pc-dashboard-monitor.vercel.app`)
- **Backend Host:** User's Windows PC (runs as `.exe` via PyInstaller)

## What's Working
1. ✅ Frontend deployed on Vercel with new design (gauges, TempCard, etc.)
2. ✅ Frontend fetches from `/api/sensors` → Supabase REST API
3. ✅ `server.py` collects CPU usage, RAM, storage, GPU usage and pushes to Supabase
4. ✅ `sensor_readings` table exists in Supabase
5. ✅ `.exe` built at `F:\VibeCoding\PC-Dashboard-Monitor\dist\PC-Dashboard-Monitor.exe`

## Current Problem: Temperatures (CPU/GPU) show `null`/`—`

### Root Cause
- **LibreHardwareMonitor (LHM)** is installed at `C:\Users\Kauezin\Downloads\LibreHardwareMonitor\`
- LHM process runs but **WMI Provider is NOT enabled** — `root\LibreHardwareMonitor` WMI namespace is empty
- The `/WMI` command-line flag does NOT work in this version
- WMI must be enabled via LHM GUI: **Options → Enable WMI Provider** (user couldn't find this option)
- Without WMI, `read_lhm_sensors()` in `server.py` returns empty → temperatures are `null`
- GPU is **AMD Radeon RX 7600** (detected via Win32_VideoController)
- No NVIDIA GPU → `nvidia-smi` not available, `pynvml` won't work
- `psutil.sensors_temperatures()` not available on this Windows setup

### What Was Being Tried
1. **WMI approach** (current `server.py`): Queries LHM via `Get-CimInstance -Namespace "root\LibreHardwareMonitor"` — fails because WMI provider not enabled
2. **Registry hack**: Set `HKCU\SOFTWARE\LibreHardwareMonitor\EnableWMI = 1` — didn't help, LHM needs GUI toggle
3. **pythonnet/clr approach**: Installed `pythonnet` in Hermes venv (Linux) — can't use on Windows. Would need to install on Windows Python and use `LibreHardwareMonitorLib.dll` directly
4. **LHM HTTP API**: Port 8085 not responding (web server not enabled in LHM)

### Key Code Locations
- `server.py` lines 84-115: `read_lhm_sensors()` — WMI query for LHM temperature sensors
- `server.py` lines 222-263: `read_cpu_temp()` — tries psutil → LHM WMI → WMI thermal zone
- `server.py` lines 118-184: `read_gpu_wmi()` — GPU usage via Get-Counter, temp via LHM
- `server.py` lines 187-219: `read_gpu()` — tries pynvml → pyamdgpuinfo → WMI fallback

## Immediate Next Steps (pick one)

### Option A: Enable LHM WMI Provider via GUI
1. Open LibreHardwareMonitor
2. Look in the menu bar or right-click context menu for "Options" or "Settings"
3. Find and enable "Enable WMI Provider" or "Remote Web Server"
4. Restart LHM
5. Test with: `Get-CimInstance -Namespace "root\LibreHardwareMonitor" -ClassName "Sensor" | Where-Object { $_.SensorType -eq "Temperature" }`

### Option B: Use pythonnet on Windows Python
1. Find Windows Python at `C:\Users\Kauezin\AppData\Local\Programs\Python\Python311\python.exe` (or similar)
2. Install pythonnet: `pip install pythonnet`
3. Use `clr.AddReference("LibreHardwareMonitorLib")` to read sensors directly
4. No LHM GUI needed — the DLL reads hardware directly

### Option C: Use OpenHardwareMonitor instead
- OHM has better WMI support out of the box
- Replace LHM WMI namespace with `root\OpenHardwareMonitor`

## Git State
- Branch: `main`, up to date with `origin/main`
- Last commit: `f852ad9 fix: frontend uses /api/sensors route (Supabase proxy), improved temp reading order`
- Untracked: `test_temp.py`, `test_temp2.py`, `test_lhm*.py`, `start_lhm*.py`, `run_lhm.sh`

## Environment Notes
- Hermes runs in MSYS/Git Bash on Windows
- `cmd //c` needed for Windows commands with `/flags`
- Python in Hermes venv is Linux — can't test Windows-specific code there
- Windows Python may be at `C:\Users\Kauezin\AppData\Local\Programs\Python\`
- Supabase credentials in `.env` file (not readable — secret)

## Files to Review
- `F:\VibeCoding\PC-Dashboard-Monitor\server.py` — main backend
- `F:\VibeCoding\PC-Dashboard-Monitor\dashboard\app\page.tsx` — frontend
- `F:\VibeCoding\PC-Dashboard-Monitor\dashboard\app\api\sensors\route.ts` → Supabase proxy
- `F:\VibeCoding\PC-Dashboard-Monitor\dashboard\components\TempCard.tsx` — temperature display
- `F:\VibeCoding\PC-Dashboard-Monitor\dashboard\components\GaugeCard.tsx` — gauge with temp badge
