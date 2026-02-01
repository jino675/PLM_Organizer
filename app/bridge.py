import time
import threading
import re
import os
import win32gui
import win32process
import win32api
import win32con
from app.context import ContextManager

class TitleBridge(threading.Thread):
    """
    Background thread that scans window titles to catch metadata 
    from the Chrome Extension via the 'Ghost Title' trick.
    """
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.context_manager = ContextManager()
        self.running = True
        # Pattern: [PLM_CTX:ID|Title] - Greedy for title (captures until the LAST ']')
        self.pattern = re.compile(r'^\[PLM_CTX:([^|]{1,30})\|(.*)\](?:\s|$)')
        self.last_sync_tag = ""

    def _get_process_name(self, hwnd):
        """Robustly retrieve the executable name of the window's process."""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            # PROCESS_QUERY_INFORMATION (0x0400) | PROCESS_VM_READ (0x0010)
            handle = win32api.OpenProcess(0x0410, False, pid)
            if handle:
                try:
                    path = win32process.GetModuleFileNameEx(handle, 0)
                    return os.path.basename(path).lower()
                finally:
                    win32api.CloseHandle(handle)
        except:
            pass
        return ""

    def run(self):
        # Silence premature print to prevent pythonw window popup
        while self.running:
            try:
                # OPTIMIZATION (v1.7.2):
                # Instead of scanning ALL windows (EnumWindows), only check the Foreground Window.
                # This drastically reduces CPU usage and meets the "Only when focused" requirement.
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        match = self.pattern.search(title)
                        if match:
                            sync_tag = match.group(0)
                            # Only update if the tag is different OR if we need to refresh
                            if sync_tag != self.last_sync_tag:
                                id_val = match.group(1)
                                title_val = match.group(2)
                                
                                # Update context
                                data = {
                                    "defect_id": id_val if id_val.startswith("DF") else "",
                                    "plm_id": id_val if not id_val.startswith("DF") else "",
                                    "title": title_val,
                                    "url": "Ghost Bridge (Active Window)"
                                }
                                print(f"Ghost Bridge: Synced from active window -> {id_val}")
                                self.context_manager.update_context(data)
                                self.last_sync_tag = sync_tag
                        else:
                            # v1.8.1 ROBUST DETECTION (Process-based)
                            # Company environments often sanitize window titles (e.g. remove "Google Chrome").
                            # We must check the ACTUAL PROCESS NAME to be 100% sure.
                            proc_name = self._get_process_name(hwnd)
                            browser_exes = ["chrome.exe", "msedge.exe", "whale.exe", "firefox.exe", "brave.exe"]
                            
                            is_browser = proc_name in browser_exes
                            
                            if is_browser:
                                # We are in a browser, but no PLM tag -> We are on a non-PLM site.
                                # Prevent Stale Context: Clear it.
                                if self.last_sync_tag != "CLEARED":
                                    print(f"Ghost Bridge: Browser Process ({proc_name}) active but no PLM tag. Clearing context.")
                                    self.context_manager.clear()
                                    self.last_sync_tag = "CLEARED"
                
                time.sleep(0.2) # Fast poll, but now extremely lightweight (O(1))
            except Exception as e:
                print(f"Title Bridge Error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
