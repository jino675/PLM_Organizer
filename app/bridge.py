import time
import threading
import re
import win32gui
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
        # Pattern: [PLM_CTX:ID|Title] - Strict limits to avoid capturing code blocks
        self.pattern = re.compile(r'\[PLM_CTX:([^|\]]{1,30})\|([^\]]{1,100})\]')
        self.last_sync_tag = ""

    def run(self):
        print("Ghost Title Bridge started...")
        while self.running:
            try:
                titles = []
                def enum_callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            titles.append(title)
                
                win32gui.EnumWindows(enum_callback, None)

                for title in titles:
                    match = self.pattern.search(title)
                    if match:
                        sync_tag = match.group(0)
                        if sync_tag != self.last_sync_tag:
                            id_val = match.group(1)
                            title_val = match.group(2)
                            
                            # Update context
                            data = {
                                "defect_id": id_val if id_val.startswith("DF") else "",
                                "plm_id": id_val if not id_val.startswith("DF") else "",
                                "title": title_val,
                                "url": "Ghost Bridge (Title)"
                            }
                            print(f"Ghost Bridge: Synced from title -> {id_val}")
                            self.context_manager.update_context(data)
                            self.last_sync_tag = sync_tag
                            break # Found one, good for this poll
                
                time.sleep(1.0) # Poll every second
            except Exception as e:
                print(f"Title Bridge Error: {e}")
                time.sleep(2)

    def stop(self):
        self.running = False
