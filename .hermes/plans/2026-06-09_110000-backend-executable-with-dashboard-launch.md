# Backend Executable with Dashboard Launch Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create a standalone Windows executable that:
1. Runs the PC-Dashboard backend sensor collector silently in background
2. Launches the user's default browser to the Vercel dashboard URL
3. Lives in the system tray for easy access and control
4. Requires no installation - just double-click to run

**Architecture:**
- Backend: Modified server.py running as invisible subprocess
- System tray: Using pystray for icon and menu
- Dashboard launch: Opens browser to pc-dashboard-monitor.vercel.app on startup
- Packaging: PyInstaller with all necessary dependencies

**Tech Stack:** Python 3.11, PyInstaller, pystray, psutil, supabase

---

### Task 1: Prepare Backend for Silent Execution

**Objective:** Modify server.py to support background operation without console window when launched from executable.

**Files:**
- Modify: `F:\VibeCoding\PC-Dashboard-Monitor/server.py`

**Step 1: Add background mode detection**
Add a command-line argument `--background` that:
- Disables console logging
- Runs sensor loop without print statements (except errors)
- Returns immediately from main() after starting thread

**Step 2: Implement background mode**
```python
# Add near top of server.py after imports
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--background', action='store_true', 
                       help='Run in background mode (no console output)')
    return parser.parse_args()

# Modify main() function:
def main():
    args = parse_args()
    
    if not args.background:
        print(f"[SensorDash] Starting HTTP sensor collector on port {PORT}...")
        print(f"  NVIDIA: {NVIDIA_AVAILABLE} | AMD: {AMD_AVAILABLE}")
        print(f"  Cooldown: {COOLDOWN}s")
        print(f"  Supabase: {'enabled' if SUPABASE_URL else 'disabled'}")

    # Start sensor collection thread
    sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
    sensor_thread.start()

    if not args.background:
        # Start HTTP server (only in foreground mode)
        server = HTTPServer((\"0.0.0.0\", PORT), Handler)
        print(f\"[SensorDash] Running at http://localhost:{PORT}/api/sensors\")
        print(f\"[SensorDash] Press Ctrl+C to stop.\")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print(\"\\n[SensorDash] Shutting down...\")
            server.shutdown()
    else:
        # In background mode, just keep the thread alive
        try:
            while True:
                time.sleep(3600)  # Sleep in 1-hour chunks
        except KeyboardInterrupt:
            pass
```

**Step 3: Test background mode**
Run: `python server.py --background & sleep 2 && curl -s http://localhost:8080/health`
Expected: `{"status": "ok"}`

**Step 4: Commit**
```bash
git add server.py
git commit -m "feat: add background mode for executable operation"
```

### Task 2: Create System Tray Launcher

**Objective:** Create a launcher that runs backend in background, shows tray icon, and launches dashboard.

**Files:**
- Create: `F:\VibeCoding\PC-Dashboard-Monitor/resources/icon.ico` (simple 64x64 icon)
- Create: `F:\VibeCoding\PC-Dashboard-Monitor/tray_launcher.py`

**Step 1: Create resources directory and icon**
```bash
mkdir -p resources
# We'll create a simple icon programmatically in the launcher
```

**Step 2: Write tray_launcher.py**
```python
import sys
import os
import subprocess
import threading
import time
import webbrowser
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import logging
from pathlib import Path

# Configure logging to file only (no console)
log_file = Path(__file__).parent / "pcdashboard.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.NullHandler()  # No console output
    ]
)
logger = logging.getLogger('PCDashboardTray')

class PCDashboardLauncher:
    def __init__(self):
        self.backend_process = None
        self.icon = None
        self.project_dir = Path(__file__).parent.absolute()
        
    def create_icon(self):
        """Create a simple dashboard icon"""
        # Create a 64x64 image with a simple gauge-like design
        image = Image.new('RGB', (64, 64), color='#2c3e50')  # Dark blue background
        draw = ImageDraw.Draw(image)
        
        # Draw a simple circle gauge
        draw.ellipse([8, 8, 56, 56], outline='#ecf0f1', width=2)
        draw.arc([12, 12, 52, 52], start=0, end=270, fill='#e74c3c', width=4)  # Red arc
        draw.text((22, 28), "PC", fill='#ecf0f1', font=None)
        draw.text((20, 40), "Dash", fill='#ecf0f1', font=None)
        
        return image
        
    def show_dashboard(self, icon, item):
        """Open the dashboard in default browser"""
        dashboard_url = "https://pc-dashboard-monitor.vercel.app"
        logger.info(f"Opening dashboard: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
    def show_logs(self, icon, item):
        """Show the log file in default text editor"""
        log_path = self.project_dir / "pcdashboard.log"
        if log_path.exists():
            logger.info(f"Opening log file: {log_path}")
            os.startfile(str(log_path))  # Windows only
        else:
            logger.warning("Log file not found")
            
    def exit_app(self, icon, item):
        """Clean up and exit"""
        logger.info("Shutting down PC Dashboard Monitor...")
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        if self.icon:
            self.icon.stop()
        sys.exit(0)
        
    def run_backend(self):
        """Run the backend server in background mode"""
        try:
            backend_path = self.project_dir / "server.py"
            logger.info(f"Starting backend: {backend_path} --background")
            
            self.backend_process = subprocess.Popen(
                [sys.executable, str(backend_path), "--background"],
                cwd=str(self.project_dir),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT  # Combine stdout/stderr
            )
            logger.info(f"Backend started (PID: {self.backend_process.pid})")
            self.backend_process.wait()
        except Exception as e:
            logger.error(f"Backend process error: {e}")
        finally:
            logger.info("Backend process terminated")
            
    def run(self):
        """Run the tray application"""
        # Start backend in background thread
        backend_thread = threading.Thread(target=self.run_backend, daemon=True)
        backend_thread.start()
        logger.info("Backend thread started")
        
        # Give backend a moment to start
        time.sleep(2)
        
        # Launch dashboard on startup
        logger.info("Launching dashboard on startup...")
        webbrowser.open("https://pc-dashboard-monitor.vercel.app")
        
        # Create tray icon
        menu = (
            item('Open Dashboard', self.show_dashboard),
            item('View Logs', self.show_logs),
            item('Exit', self.exit_app)
        )
        
        self.icon = pystray.Icon(
            "PC-Dashboard-Monitor",
            self.create_icon(),
            "PC Dashboard Monitor",
            menu
        )
        
        logger.info("Starting system tray application...")
        self.icon.run()

if __name__ == "__main__":
    app = PCDashboardLauncher()
    app.run()
```

**Step 3: Test tray launcher**
Run: `python tray_launcher.py`
Expected:
- No console window appears
- Tray icon shows in system tray
- Default browser opens to Vercel dashboard
- Right-click menu works: Open Dashboard, View Logs, Exit
- Backend collects data (verify via logs or Supabase)

**Step 4: Commit**
```bash
git add resources/ tray_launcher.py
git commit -m "feat: add system tray launcher with dashboard launch"
```

### Task 3: Update PyInstaller Spec for Full Executable

**Objective:** Configure PyInstaller to build the tray launcher as the main executable.

**Files:**
- Modify: `F:\VibeCoding/PC-Dashboard-Monitor/PC-Dashboard-Monitor.spec`

**Step 1: Update spec to use tray launcher**
```python
# Change Analysis to use tray_launcher.py
a = Analysis(
    ['tray_launcher.py'],  # <-- MAIN ENTRY POINT
    pathex=[],
    binaries=[],
    datas=[
        ('.env.example', '.'),
        ('resources', 'resources'),  # Include icon and other resources
    ],
    hiddenimports=[
        'psutil',
        'pynvml', 
        'pyamdgpuinfo',
        'supabase',
        'pystray',
        'PIL.Image',
        'PIL.ImageDraw',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ... rest remains the same ...

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PC-Dashboard-Monitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # CRITICAL: Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',  # Use our custom icon
)
```

**Step 2: Build the executable**
Run: `pyinstaller --noconfirm --clean PC-Dashboard-Monitor.spec`
Expected: Successful build in `dist/PC-Dashboard-Monitor/`

**Step 3: Test the executable**
Run: `dist/PC-Dashboard-Monitor/PC-Dashboard-Monitor.exe`
Expected:
- No console window flashes or appears
- Tray icon appears in system tray
- Default browser opens to Vercel dashboard
- Right-click menu functional
- Backend runs silently (check logs or Supabase for data updates)
- Exit from tray menu works cleanly

**Step 4: Verify auto-start capability (optional)**
The executable can be placed in Windows Startup folder:
`shell:startup` -> Create shortcut to PC-Dashboard-Monitor.exe

**Step 5: Commit**
```bash
git add PC-Dashboard-Monitor.spec
git commit -m "feat: build successful executable with dashboard launch"
```

### Task 4: Final Documentation and Validation

**Objective:** Create user-facing documentation and perform final validation.

**Files:**
- Create: `F:\VibeCoding/PC-Dashboard-Monitor/docs/EXECUTABLE_README.md`

**Content:**
```markdown
# PC Dashboard Monitor - Standalone Executable

## What This Does
Double-clicking `PC-Dashboard-Monitor.exe` will:
1. 📊 Start collecting sensor data from your PC (CPU, GPU, RAM, Storage)
2. 🌐 Open your browser to the live dashboard at pc-dashboard-monitor.vercel.app
3. ⚙️ Run silently in your system tray (bottom-right corner)
4. 💾 Send data to your Supabase database every 5 seconds

## First-Time Setup
1. Download the executable from the latest release
2. Place it in a permanent folder (e.g., `C:\Tools\PC-Dashboard\`)
3. Double-click to run - it will:
   - Automatically create a `pcdashboard.log` file in the same directory
   - Open your browser to the dashboard
   - Show a purple icon in your system tray

## System Tray Menu
Right-click the tray icon for:
- **Open Dashboard** - (Re)opens your browser to the live dashboard
- **View Logs** - Opens the detailed log file for troubleshooting
- **Exit** - Stops data collection and closes the application

## Configuration
The executable looks for a `.env` file in the same directory:
- If not found, it uses hardcoded Supabase credentials (configured for your project)
- To use your own Supabase project, create `.env` with:
  ```
  SUPABASE_URL=your_project_url
  SUPABASE_KEY=your_service_role_key
  ```

## Data Privacy
- Sensor data stays on your PC until sent to YOUR Supabase database
- No data is sent to any third-party services
- You retain full ownership and control of your data

## Troubleshooting
- **No icon appears?** Check if antivirus is blocking it (add exception)
- **Dashboard not opening?** Try running as administrator once
- **No data updating?** Check `pcdashboard.log` for errors
- **Want to stop temporarily?** Use tray icon → Exit, then restart when needed

## Backup & Portability
- Copy the entire folder to another Windows PC to move your setup
- The `.env` file (if you created one) contains your Supabase credentials
- Log file grows over time - safe to delete periodically
```

**Step 1: Create docs directory and file**
```bash
mkdir -p docs
# Write EXECUTABLE_README.md
```

**Step 2: Final validation checklist**
Run through all verification steps:
- [ ] Executable builds without warnings
- [ ] No console window visible when running
- [ ] Tray icon appears and is functional
- [ ] Dashboard launches on startup
- [ ] Backend collects and sends data (verify via Supabase)
- [ ] Exit function works cleanly
- [ ] Log file is created and populated
- [ ] Works after fresh download (no dependencies needed)

**Step 3: Commit**
```bash
git add docs/EXECUTABLE_README.md
git commit -m "docs: add executable user guide"
```

## Risks, Tradeoffs, and Open Questions

**Risks:**
- Antivirus false positives (common with PyInstaller executables)
- Icon may not display correctly on all Windows themes
- Log file could grow indefinitely (mitigated by user cleanup)

**Tradeoffs:**
- Using browser launch vs embedded dashboard: Simpler, leverages existing Vercel deployment
- Backend-only executable: Would require building frontend separately (more complex)
- Electron/neutralino approach: Much larger file size, more complex build

**Open Questions:**
1. Should we include a .env.example in the executable folder? (Yes, done via datas)
2. Should we add version checking or auto-update? (Out of scope v1)
3. Should we allow configuring dashboard URL via .env? (Could be added later)

## Files Changed
- server.py (added --background mode)
- New: tray_launcher.py, resources/icon.ico
- Modified: PC-Dashboard-Monitor.spec
- New: docs/EXECUTABLE_README.md

## Validation Steps
1. [ ] `pyinstaller` completes without missing module warnings
2. [ ] Executable runs: no console, tray icon appears
3. [ ] Browser opens to correct dashboard URL on startup
4. [ ] Tray menu items all function correctly
5. [ ] Backend collects sensor data (verify logs: "SensorDash" entries)
6. [ ] Data appears in Supabase dashboard within 10-15 seconds
7. [ ] Exit from tray menu terminates all processes cleanly
8. [ ] Log file created with appropriate entries
9. [ ] Executable runs on clean Windows VM (no Python installed)

**Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?**