import sys
import os
import io

# 0. EARLY STEALTH: Redirect stdout/stderr immediately to suppress popup windows
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()

import threading
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from app.gui import MainWindow
from app.server import start_server
from app.watcher import FileWatcher

def log_uncaught_exceptions(ex_cls, ex, tb):
    """Global handler for unhandled exceptions."""
    err_msg = "".join(traceback.format_exception(ex_cls, ex, tb))
    print(f"CRITICAL ERROR:\n{err_msg}")
    try:
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{socket.gethostname()}] {'='*40}\n")
            f.write(err_msg)
    except:
        pass
    
sys.excepthook = log_uncaught_exceptions

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def main():
    # Fix Taskbar Icon on Windows
    myappid = 'jino.plm.organizer.v1'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    # Application Setup
    app = QApplication(sys.argv)
    app.setApplicationName("PLM Organizer")
    
    # Set Persistent App Icon
    icon_path = os.path.join(os.path.dirname(__file__), "app", "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Dynamic Port Allocation (5555-5564)
    server_port = 5555
    found_port = False
    
    for port in range(5555, 5565):
        if not is_port_in_use(port):
            server_port = port
            found_port = True
            break
            
    if not found_port:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Startup Error")
        msg.setText("Could not find an available port (5555-5564).")
        msg.setInformativeText("Please close other instances of PLM Organizer.")
        msg.exec()
        sys.exit(1)

    if server_port != 5555:
        # Use a silent log for startup info when running headless
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{socket.gethostname()}] Port 5555 busy. Using port {server_port}.\n")
    
    # Initialize Core Components
    # 1. Config/Settings
    # 2. Server for Browser Comms
    server_thread = threading.Thread(target=start_server, args=(server_port,), daemon=True)
    server_thread.start()
    
    # 3. File Watcher
    watcher = FileWatcher()
    watcher.start()
    
    # 4. Ghost Title Bridge (Invisible Sync)
    from app.bridge import TitleBridge
    bridge = TitleBridge()
    bridge.start()
    
    # 5. GUI
    window = MainWindow(watcher, server_port)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
