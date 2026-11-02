"""
Fuel Bunk Manager - Offline Edition Unified Launcher
Usage:
  python main.py          -> Launches the Offline Web Application in default browser
  python main.py --gui    -> Launches the Native Windows Desktop GUI
  python main.py --web    -> Launches the Offline Web Application
  python main.py --sync   -> Imports / syncs cloud records into local SQLite database
"""

import sys
import os

from database import init_db

def main():
    init_db()
    args = sys.argv[1:]

    if "--gui" in args:
        print("Starting Native Windows Desktop GUI...")
        from desktop_gui import FuelBunkApp
        app = FuelBunkApp()
        app.mainloop()
    elif "--sync" in args:
        print("Importing cloud data into offline database...")
        from import_cloud_data import import_all
        import_all()
    else:
        # Default: Launch Offline Web Server + Browser
        print("Starting Offline Web Dashboard...")
        from offline_server import start_server, PORT
        start_server(PORT, open_browser=True)

if __name__ == "__main__":
    main()
