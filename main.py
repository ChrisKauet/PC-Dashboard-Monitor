"""
PC Dashboard Monitor — System Tray Executable
Launches sensor collection in background + system tray icon + opens browser dashboard.
"""
import os
import sys
import time
import json
import logging
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    input("Error: Install pystray + pillow (pip install pystray pillow). Press Enter to exit...")
    sys.exit(1)

import sensors

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── Environment setup ─────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_env():
    env_path = os.path.join(get_base_dir(), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


load_env()

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://pc-dashboard-monitor.vercel.app")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
PUSH_INTERVAL = float(os.environ.get("PUSH_INTERVAL_SECONDS", "5"))
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")


# ── Startup validation ────────────────────────────────────────────
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning(
        "SUPABASE_URL or SUPABASE_KEY not set — sensor data will NOT be pushed remotely. "
        "Check your .env file."
    )


# ── Supabase push (with error logging) ───────────────────────────
_supabase_client = None
_supabase_fail_logged = False


def push_to_supabase(data: dict) -> None:
    global _supabase_client, _supabase_fail_logged
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    if _supabase_client is None:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            _supabase_fail_logged = False
        except Exception as e:
            if not _supabase_fail_logged:
                logger.error("Failed to create Supabase client: %s", e)
                _supabase_fail_logged = True
            return
    try:
        record = {
            "cpu_usage": data.get("cpu_usage"),
            "cpu_temp": data.get("cpu_temp"),
            "cpu_cores": json.dumps(data.get("cpu_cores", [])),
            "gpu_usage": data.get("gpu_usage"),
            "gpu_temp": data.get("gpu_temp"),
            "vram_used": data.get("vram_used"),
            "vram_total": data.get("vram_total"),
            "gpu_fan_rpm": data.get("gpu_fan_rpm"),
            "ram_used": data.get("ram_used"),
            "ram_total": data.get("ram_total"),
            "ram_usage": data.get("ram_usage"),
            "storage": json.dumps(data.get("storage", [])),
            "uptime_sec": data.get("uptime_sec"),
            "hostname": data.get("hostname"),
            "gpu_vendor": data.get("gpu_vendor"),
        }
        _supabase_client.table("sensor_readings").insert(record).execute()
        _supabase_fail_logged = False
    except Exception as e:
        if not _supabase_fail_logged:
            logger.error("Supabase push failed: %s", e)
            _supabase_fail_logged = True


# ── Sensor loop ───────────────────────────────────────────────────
_latest_data: dict = {"status": "initializing"}
_data_lock = threading.Lock()
_running = True


def sensor_loop() -> None:
    global _latest_data
    while _running:
        try:
            data = sensors.collect()
            data["status"] = "online"
            with _data_lock:
                _latest_data = data
            push_to_supabase(data)
        except Exception as e:
            logger.error("Sensor collection error: %s", e)
            with _data_lock:
                _latest_data = {"status": "error", "error": str(e)}
        time.sleep(PUSH_INTERVAL)


# ── HTTP server ───────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/api/sensors", "/api/sensors/"):
            with _data_lock:
                payload = json.dumps(dict(_latest_data)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
            self.end_headers()
            self.wfile.write(payload)
        elif self.path in ("/health", "/health/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_):
        pass


def http_server() -> None:
    port = 8080
    while True:
        try:
            # Bind to 127.0.0.1 (localhost only) — prevents LAN exposure
            srv = HTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    logger.info("HTTP API listening on 127.0.0.1:%d", port)
    srv.serve_forever()


# ── System tray ───────────────────────────────────────────────────
_icon = None


def _create_tray_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rectangle([12, 12, 52, 48], fill="#4a90e2", outline="#357ab8", width=2)
    dc.rectangle([26, 48, 38, 58], fill="#4a90e2")
    dc.polygon([(16, 16), (28, 16), (16, 28)], fill=(255, 255, 255, 100))
    return img


def _open_dashboard(_icon=None, _item=None):
    webbrowser.open(DASHBOARD_URL)


def _open_api(_icon=None, _item=None):
    webbrowser.open("http://127.0.0.1:8080/api/sensors")


def _on_quit(icon_ref, _item):
    global _running
    _running = False
    icon_ref.stop()


# ── Entry point ───────────────────────────────────────────────────
def main():
    threading.Thread(target=sensor_loop, daemon=True).start()
    threading.Thread(target=http_server, daemon=True).start()
    time.sleep(1)
    _open_dashboard()

    global _icon
    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", _open_dashboard),
        pystray.MenuItem("View Local API", _open_api),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", _on_quit),
    )
    _icon = pystray.Icon("PCDashboard", _create_tray_image(), "PC Dashboard Monitor", menu)
    _icon.run()


if __name__ == "__main__":
    main()
