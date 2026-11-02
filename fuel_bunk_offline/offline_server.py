"""
Fuel Bunk Manager - Offline Local Web Server
Runs 100% locally with Python standard library (http.server).
Zero external dependencies, zero cloud connection required.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import webbrowser
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import (
    init_db, get_settings, set_setting, get_staff_list, authenticate_staff, save_staff,
    get_last_closing, save_shift, get_shifts, get_shift_by_id, delete_shift,
    get_calendar_analysis, save_stock_purchase, get_stock_purchases,
    backup_database, list_backups, restore_database
)

PORT = 8085
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "app.html")

class OfflineRequestHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and disable caching so every local update is instant
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path.lower()

        if path in ("/", "/index.html", "/app", "/desktop.html", "/mobile.html"):
            if not os.path.isfile(TEMPLATE_FILE):
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Template file not found.")
                return

            with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        if path == "/api/status":
            self.send_json({"ok": True, "status": "online", "mode": "100% Offline Python Engine", "port": PORT})
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8"))
        except Exception:
            body = {}

        action = body.get("action") or ""
        url = urllib.parse.urlparse(self.path)
        if not action and "action" in urllib.parse.parse_qs(url.query):
            action = urllib.parse.parse_qs(url.query)["action"][0]

        resp = self.handle_action(action, body)
        self.send_json(resp)

    def send_json(self, data, status=200):
        out = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(out)

    def handle_action(self, action, body):
        try:
            if action == "loginUser":
                sid = body.get("staffId") or body.get("Staff_ID")
                pin = body.get("pin") or body.get("PIN")
                user = authenticate_staff(sid, pin)
                if user:
                    return {"ok": True, "user": user}
                return {"ok": False, "error": "Invalid Staff ID or 4-Digit PIN"}

            elif action == "getStaff":
                active_only = bool(body.get("activeOnly"))
                staff = get_staff_list(active_only)
                return {"ok": True, "staff": staff}

            elif action == "saveStaff":
                save_staff(body.get("staff") or body)
                return {"ok": True, "message": "Staff member saved"}

            elif action == "getPumps":
                return {
                    "ok": True,
                    "pumps": [
                        {"Pump_No": "1", "Pump_Name": "Pump 1", "Nozzle_1": "MS Nozzle 1 / HSD Nozzle 1", "Nozzle_2": "MS Nozzle 2 / HSD Nozzle 2"},
                        {"Pump_No": "2", "Pump_Name": "Pump 2", "Nozzle_1": "MS Nozzle 1 / HSD Nozzle 1", "Nozzle_2": "MS Nozzle 2 / HSD Nozzle 2"},
                        {"Pump_No": "3", "Pump_Name": "Pump 3", "Nozzle_1": "CNG Nozzle 1", "Nozzle_2": "CNG Nozzle 2"}
                    ]
                }

            elif action == "getLastClosing":
                p = int(body.get("pumpNo") or body.get("Pump_No") or 1)
                dt = body.get("date")
                res = get_last_closing(p, dt)
                return {
                    "ok": True,
                    "lastClosing": res,
                    "closing": res["closing"]
                }

            elif action == "saveShift":
                d = body.get("data") or body
                res = save_shift(d)
                return res

            elif action == "getShifts":
                shifts = get_shifts(
                    date_from=body.get("dateFrom"),
                    date_to=body.get("dateTo"),
                    pump_no=body.get("pumpNo"),
                    staff_id=body.get("staffId")
                )
                return {"ok": True, "shifts": shifts}

            elif action == "getShift":
                sid = body.get("shiftId")
                s = get_shift_by_id(sid)
                if s:
                    return {"ok": True, "shift": s}
                return {"ok": False, "error": "Shift not found"}

            elif action == "updateShift":
                d = body.get("data") or body
                sid = body.get("shiftId") or d.get("Shift_ID") or d.get("shift_id")
                d["shift_id"] = sid
                res = save_shift(d)
                return res

            elif action == "deleteShift":
                sid = body.get("shiftId") or body.get("Shift_ID")
                delete_shift(sid)
                return {"ok": True, "message": "Shift deleted successfully"}

            elif action == "getCalendarData":
                yr = int(body.get("year") or datetime.now().year)
                mo = int(body.get("month") or datetime.now().month)
                cal = get_calendar_analysis(yr, mo)
                return {"ok": True, "year": yr, "month": mo, "calendar": cal}

            elif action == "getStockPurchases":
                purchases = get_stock_purchases()
                return {"ok": True, "purchases": purchases}

            elif action == "saveStockPurchase":
                res = save_stock_purchase(body.get("data") or body)
                return res

            elif action == "getSettings":
                return {"ok": True, "settings": get_settings()}

            elif action == "saveSetting":
                k = body.get("key")
                v = body.get("value")
                set_setting(k, v)
                return {"ok": True, "message": "Setting saved"}

            elif action == "backupDb":
                res = backup_database()
                return res

            elif action == "listBackups":
                return {"ok": True, "backups": list_backups()}

            elif action == "restoreDb":
                fn = body.get("filename")
                res = restore_database(fn)
                return res

            else:
                return {"ok": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

def start_server(port=PORT, open_browser=True):
    init_db()
    os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
    
    server_address = ("127.0.0.1", port)
    
    # Try preferred port, fallback to port+1 if busy
    try:
        httpd = socketserver.TCPServer(server_address, OfflineRequestHandler)
    except OSError:
        port = port + 1
        server_address = ("127.0.0.1", port)
        httpd = socketserver.TCPServer(server_address, OfflineRequestHandler)

    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print(f" Fuel Bunk Manager - 100% Offline Python Server Active")
    print(f" URL: {url}")
    print(f" Database: {os.path.join(BASE_DIR, 'fuel_bunk.db')}")
    print("=" * 60)
    print(" Press Ctrl+C in this terminal window to stop the server.")

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping offline server...")
        httpd.server_close()
        print("Server stopped cleanly.")

if __name__ == "__main__":
    start_server(PORT, open_browser=True)
