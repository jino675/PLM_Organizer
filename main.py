import sys
import threading
import traceback
import os
import ctypes

# 0. EARLY STEALTH: Redirect stdout/stderr only if we are in pythonw (noconsole) mode
# To be truly safe, we'll use a dummy writer that doesn't crash
class SilentWriter:
    def write(self, *args, **kwargs): pass
    def flush(self): pass

if sys.executable.endswith("pythonw.exe"):
    sys.stdout = SilentWriter()
    sys.stderr = SilentWriter()

def log_uncaught_exceptions(ex_cls, ex, tb):
    """Global handler for unhandled exceptions."""
    err_msg = "".join(traceback.format_exception(ex_cls, ex, tb))
    # Try print (might be silent)
    try:
        print(f"CRITICAL ERROR:\n{err_msg}")
    except: pass
    
    # Always write to file
    try:
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{os.environ.get('COMPUTERNAME', 'UNKNOWN')}] {'='*40}\n")
            f.write(err_msg)
    except:
        pass
    
sys.excepthook = log_uncaught_exceptions

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.gui import MainWindow
from app.watcher import FileWatcher

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
    
    # Initialize Core Components
    # 1. Server Removed (v1.7.1 - Ghost Bridge Only)

    # 2. File Watcher
    watcher = FileWatcher()
    # watcher.start() -> Deformed to GUI for validation logic
    
    # 3. Ghost Title Bridge (Invisible Sync)
    from app.bridge import TitleBridge
    bridge = TitleBridge()
    bridge.start()
    
    # 4. GUI
    window = MainWindow(watcher)
    window.show()
    
    exit_code = app.exec()
    
    # v1.8.1: Strict Shutdown
    # Force kill all threads (including TitleBridge) to prevent zombie processes.
    print("[Main] Shutting down...")
    os._exit(exit_code) # os._exit is stronger than sys.exit

if __name__ == "__main__":
    main()
