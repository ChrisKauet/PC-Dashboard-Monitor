"""
System Tray Launcher for PC Dashboard Monitor
Runs the backend sensor collector in background and shows system tray icon.
"""
import os
import sys
import subprocess
import signal
import webbrowser

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: pystray and pillow required. Run: pip install pystray pillow")
    sys.exit(1)

DASHBOARD_URL = "https://pc-dashboard-monitor.vercel.app"
LOG_FILE = os.path.join(os.path.expanduser("~"), ".pcdashboard", "server.log")

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_SCRIPT = os.path.join(BASE_DIR, "server_py", "server.exe")

server_process = None
icon = None


def create_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rectangle([12, 12, 52, 48], fill="#4a90e2", outline="#357ab8", width=2)
    dc.rectangle([26, 48, 38, 58], fill="#4a90e2")
    dc.polygon([(16, 16), (28, 16), (16, 28)], fill=(255, 255, 255, 100))
    return img


def start_backend():
    global server_process
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        server_process = subprocess.Popen(
            [SERVER_SCRIPT, "--background"],
            cwd=os.path.dirname(SERVER_SCRIPT),
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[Tray] Backend PID {server_process.pid}")
    except Exception as e:
        print(f"[Tray] Start error: {e}")


def stop_backend():
    global server_process
    if server_process:
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()
        finally:
            server_process = None


def open_dashboard():
    webbrowser.open(DASHBOARD_URL)


def open_logs():
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    if sys.platform == "win32":
        subprocess.Popen(f'explorer "{log_dir}"', shell=True)
    else:
        webbrowser.open(f"file://{log_dir}")


def on_quit(icon_ref, item):
    stop_backend()
    icon_ref.stop()


def setup_tray():
    global icon
    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", open_dashboard),
        pystray.MenuItem("View Logs Folder", open_logs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", on_quit),
    )
    icon = pystray.Icon("PCDashboard", create_image(), "PC Dashboard Monitor", menu)
    start_backend()
    icon.run()


def main():
    signal.signal(signal.SIGINT, lambda *_: (on_quit(icon, None), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (on_quit(icon, None), sys.exit(0)))
    setup_tray()


if __name__ == "__main__":
    main()
