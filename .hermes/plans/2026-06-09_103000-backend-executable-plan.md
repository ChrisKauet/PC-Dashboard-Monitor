# Backend Executable Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Convert the PC-Dashboard backend collector into a standalone Windows executable that runs in the system tray without console window, with auto-start capability.

**Architecture:** 
- Modify existing PyInstaller spec to correctly include all dependencies (especially supabase)
- Add system tray functionality using pystray or similar library
- Create launcher script that manages backend process and tray icon
- Ensure executable reads .env file correctly and handles missing configuration gracefully
- Optional: Add Windows startup registry entry for auto-launch

**Tech Stack:** Python 3.11, PyInstaller, pystray, psutil, supabase

---

### Task 1: Fix PyInstaller Spec File

**Objective:** Correct the existing spec file to include necessary dependencies and configure for windowless executable.

**Files:**
- Modify: `F:\VibeCoding\PC-Dashboard-Monitor/PC-Dashboard-Monitor.spec`

**Step 1: Analyze current spec issues**
- Line 29: Incorrectly excludes 'supabase' (REQUIRED for backend)
- Line 53: `console=True` shows console window (should be False)
- Line 59: No icon specified
- Missing proper data file handling for .env

**Step 2: Write corrected spec**
```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for PC Dashboard Monitor Backend Executable
# Build: pyinstaller PC-Dashboard-Monitor.spec

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('.env.example', '.'),  # Include example env file
    ],
    hiddenimports=[
        'psutil',
        'pynvml', 
        'pyamdgpuinfo',
        'supabase',
        # Add system tray dependencies
        'pystray',
        'PIL.Image',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,          # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',  # Will need to create/add icon
)

# Optional: Create COLLECT step for easier debugging
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='PC-Dashboard-Monitor')
```

**Step 3: Run test to verify spec works**
Run: `cd /f/VibeCoding/PC-Dashboard-Monitor && pyinstaller --noconfirm PC-Dashboard-Monitor.spec`
Expected: Build completes without missing module errors

**Step 4: Test executable**
Run: `cd /f/VibeCoding/PC-Dashboard-Monitor/dist/PC-Dashboard-Monitor && PC-Dashboard-Monitor.exe`
Expected: Runs without console window, collects sensors, pushes to Supabase

**Step 5: Commit**
```bash
git add PC-Dashboard-Monitor.spec
git commit -m "fix: correct PyInstaller spec for executable build (include supabase, hide console)"
```

### Task 2: Add System Tray Functionality

**Objective:** Modify backend to run in system tray with show/hide console option and exit menu.

**Files:**
- Create: `F:\VibeCoding\PC-Dashboard-Monitor/resources/icon.ico` (simple icon)
- Modify: `F:\VibeCoding\PC-Dashboard-Monitor/server.py` to add tray mode
- Alternative: Create separate tray launcher

**Approach Option A: Modify server.py to support --tray flag**
**Approach Option B: Create tray_launcher.py that manages server process**

I'll choose Option B for cleaner separation.

**Step 1: Create resources folder and icon**
```bash
mkdir -p resources
# Create simple icon (can be replaced later)
```

**Step 2: Write tray_launcher.py**
```python
import sys
import os
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('PCDashboardTray')

class PCDashboardTray:
    def __init__(self):
        self.server_process = None
        self.icon = None
        self.setup_icon()
        
    def setup_icon(self):
        """Create a simple icon or load from file"""
        try:
            # Try to load existing icon
            icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
            if os.path.exists(icon_path):
                self.icon_image = Image.open(icon_path)
            else:
                # Create a simple default icon
                self.icon_image = Image.new('RGB', (64, 64), color='purple')
                draw = ImageDraw.Draw(self.icon_image)
                draw.rectangle([16, 16, 48, 48], fill='black')
        except Exception as e:
            logger.error(f"Failed to load icon: {e}")
            # Fallback to simple generated icon
            self.icon_image = Image.new('RGB', (64, 64), color='purple')
            
    def show_console(self, icon, item):
        """Show the server console window"""
        if self.server_process:
            # On Windows, we'd need to attach to console - complex
            # For now, just log
            logger.info("Console show requested (not implemented in this version)")
            
    def hide_console(self, icon, item):
        """Hide the server console window"""
        logger.info("Console hide requested (running in background)")
        
    def exit_app(self, icon, item):
        """Clean up and exit"""
        logger.info("Shutting down PC Dashboard Monitor...")
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
        if self.icon:
            self.icon.stop()
        sys.exit(0)
        
    def run_server(self):
        """Run the backend server in subprocess"""
        try:
            # Get path to server.py
            server_path = os.path.join(os.path.dirname(__file__), 'server.py')
            # Use the same python executable
            self.server_process = subprocess.Popen(
                [sys.executable, server_path],
                cwd=os.path.dirname(__file__),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            logger.info(f"Backend server started (PID: {self.server_process.pid})")
            self.server_process.wait()
        except Exception as e:
            logger.error(f"Server process error: {e}")
        finally:
            logger.info("Backend server stopped")
            
    def run(self):
        """Run the tray application"""
        # Start server in background thread
        server_thread = threading.Thread(target=self.run_server, daemon=True)
        server_thread.start()
        
        # Create tray icon
        menu = (
            item('Show Console', self.show_console),
            item('Hide Console', self.hide_console),
            item('Exit', self.exit_app)
        )
        
        self.icon = pystray.Icon(
            "PC-Dashboard-Monitor",
            self.icon_image,
            "PC Dashboard Monitor",
            menu
        )
        
        logger.info("Starting system tray application...")
        self.icon.run()

if __name__ == "__main__":
    app = PCDashboardTray()
    app.run()
```

**Step 3: Update PyInstaller spec to include tray launcher**
Modify spec to use tray_launcher.py as main script instead of server.py

**Step 4: Test tray launcher**
Run: `python tray_launcher.py`
Expected: Tray icon appears, backend runs in background, can exit via menu

**Step 5: Commit**
```bash
git add resources/ tray_launcher.py
git commit -m "feat: add system tray launcher for background execution"
```

### Task 3: Test Full Executable Build

**Objective:** Build and test the complete executable with tray functionality.

**Files:**
- Modify: `F:\VibeCoding/PC-Dashboard-Monitor/PC-Dashboard-Monitor.spec` (to use tray_launcher.py)
- Test: Build and run executable

**Step 1: Update spec for tray launcher**
Change Analysis to use ['tray_launcher.py'] instead of ['server.py']
Add resources folder to datas:
```python
datas=[
    ('.env.example', '.'),
    ('resources', 'resources'),
],
```

**Step 2: Build executable**
Run: `pyinstaller --noconfirm PC-Dashboard-Monitor.spec`
Expected: Successful build in dist/ folder

**Step 3: Test executable**
Run: `dist/PC-Dashboard-Monitor/PC-Dashboard-Monitor.exe`
Expected:
- No console window appears
- Tray icon shows in system tray
- Right-click shows menu: Show Console, Hide Console, Exit
- Backend collects data and pushes to Supabase (verify via Supabase dashboard)
- Exit menu properly terminates process

**Step 4: Verify auto-start capability (optional)**
Add registry key for auto-start:
```python
import winreg
key = winreg.HKEY_CURRENT_USER
subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as registry_key:
    winreg.SetValueEx(registry_key, "PC-Dashboard-Monitor", 0, winreg.REG_SZ, "C:\\path\\to\\exe")
```

**Step 5: Commit**
```bash
git add PC-Dashboard-Monitor.spec
git commit -m "feat: build successful executable with system tray support"
```

### Task 4: Documentation and Handoff

**Objective:** Create documentation for users on how to use the executable.

**Files:**
- Create: `F:\VibeCoding/PC-Dashboard-Monitor/docs/EXECUTABLE_USAGE.md`

**Content:**
```markdown
# PC Dashboard Monitor - Executable Usage

## Overview
This executable runs the backend sensor collector in the Windows system tray.

## Usage
1. Double-click `PC-Dashboard-Monitor.exe`
2. A purple icon will appear in your system tray
3. Right-click the icon for options:
   - Show Console: (Not fully implemented in v1)
   - Hide Console: Runs purely in background
   - Exit: Stops the application

## First Run
- On first run, the app will look for `.env` file in the same directory
- If not found, it will create an example `.env.example` you can rename and configure
- You must configure your Supabase URL and service role key in `.env`

## Configuration
Copy `.env.example` to `.env` and fill in:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_service_role_key
SENSOR_PORT=8080
SENSOR_COOLDOWN=5.0
PUSH_INTERVAL=5.0
```

## Auto-start (Optional)
To run automatically at login:
1. Press Win+R, type `shell:startup`, hit Enter
2. Create a shortcut to PC-Dashboard-Monitor.exe in this folder
```

**Step 1: Create docs directory and file**
```bash
mkdir -p docs
# Write EXECUTABLE_USAGE.md
```

**Step 2: Commit**
```bash
git add docs/EXECUTABLE_USAGE.md
git commit -m "docs: add executable usage documentation"
```

## Risks, Tradeoffs, and Open Questions

**Risks:**
- pystray may not be installed in build environment (added to hiddenimports)
- Icon loading may fail if resources not packaged correctly
- Windows Defender may flag unsigned executable (expected)

**Tradeoffs:**
- Using separate tray launcher vs modifying server.py: More files but cleaner separation
- Console window completely hidden: No easy way to see logs without adding log viewer to tray

**Open Questions:**
1. Should we include the frontend in the executable? (No, it's hosted on Vercel)
2. Should we add auto-update capability? (Out of scope for v1)
3. Should we add sensor configuration UI in tray menu? (Future enhancement)

## Files Likely to Change
- PC-Dashboard-Monitor.spec (primary)
- New: tray_launcher.py, resources/icon.ico
- Modified: server.py (may need adjustments for background operation)
- New: docs/EXECUTABLE_USAGE.md

## Validation Steps
1. [ ] Build executable succeeds without missing module warnings
2. [ ] Executable runs without console window
3. [ ] Tray icon appears and responds to right-click
4. [ ] Backend collects sensor data (verify logs or Supabase)
5. [ ] Exit menu cleanly terminates process
6. [ ] .env file handling works (creates example if missing)
7. [ ] Test on clean Windows VM if possible

**Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?**