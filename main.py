import sys
import threading
import socket
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
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
    # Application Setup
    app = QApplication(sys.argv)
    app.setApplicationName("PLM Organizer")
    
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
        # Warn user but continue
        print(f"Port 5555 busy. Using port {server_port}.")
        # Optional: Show a non-blocking toast or just log it. 
        # For now, we proceed silently as requested, assuming the extension will find it.
    
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
