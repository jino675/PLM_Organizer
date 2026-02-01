import time
import os
import json
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.organizer import Organizer

class DownloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.organizer = Organizer()

    def on_created(self, event):
        if event.is_directory:
            return
        # v1.8.7: Parallel Processing
        # Spawn thread so one large download doesn't block checking of other files
        threading.Thread(target=self.process, args=(event.src_path,), daemon=True).start()

    def on_moved(self, event):
        if event.is_directory:
            return
        # When browser finishes download (rename .crdownload -> .zip), it triggers on_moved
        threading.Thread(target=self.process, args=(event.dest_path,), daemon=True).start()

    def process(self, file_path):
        filename = os.path.basename(file_path)
        
        # 1. Ninja Mode: Check if this is a context bridge file
        # Matches "_plm_context.json" or "_plm_context (1).json" etc.
        if filename.startswith("_plm_context") and filename.endswith(".json"):
            print(f"Ninja Mode: Received context file {filename}")
            try:
                # Increased delay to ensures Chrome has finished writing/unlocking
                time.sleep(1.0) 
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    from app.context import ContextManager
                    ContextManager().update_context(data)
                
                # Instantly delete to keep the folder clean
                if os.path.exists(file_path):
                    os.remove(file_path)
                print(f"Ninja Mode: Success. Data from {data.get('url', 'Unknown URL')}")
            except Exception as e:
                print(f"Ninja Mode Error (File may be locked or malformed): {e}")
            return

        # 2. Ignore other temporary download files
        ignored_exts = ['.crdownload', '.tmp', '.download', '.irx', '.partial', '.part']
        if any(filename.lower().endswith(ext) for ext in ignored_exts):
            return
        
        # 3. Regular File Processing
        print(f"New file detected: {file_path}")
        
        # 4. Verification Loop: Wait for file to be truly ready (Stable Size & Not Locked)
        if self.wait_for_file_ready(file_path):
            self.organizer.organize_file(file_path)
        else:
            print(f"Skipping {filename}: File verification failed (Locked or Unstable).")

    def is_folder_busy(self, target_file_path, window_seconds=3.0):
        """
        Checks if ANY other file in the directory has been modified recently.
        Used to detect if a batch download is in progress.
        """
        try:
            folder = os.path.dirname(target_file_path)
            now = time.time()
            
            # Fast scan using os.scandir
            with os.scandir(folder) as it:
                for entry in it:
                    if not entry.is_file(): continue
                    if entry.path == target_file_path: continue # Don't check self
                    
                    # Ignore partial files (they are obviously busy but we ignore them elsewhere)
                    if any(entry.name.lower().endswith(ext) for ext in ['.crdownload', '.tmp', '.part']):
                        # However, a .crdownload updating MEANS the folder is busy!
                        # So actually we SHOULD check them.
                        pass 

                    try:
                        # Check modification time
                        if now - entry.stat().st_mtime < window_seconds:
                            # Found an active neighbor!
                            return True
                    except OSError:
                        pass # File locked or gone, ignore
        except Exception:
            pass
        return False

    def wait_for_file_ready(self, file_path, check_interval=0.2, stability_checks=3, lock_retries=50):
        """
        Ensures file is ready by:
        1. Checking size stability (no changes for 'stability_checks' intervals).
        2. Checking file lock (can we rename it?).
        """
        last_size = -1
        stable_count = 0
        zero_byte_retries = 0
        max_zero_byte_retries = 25 # 25 * 0.2s = 5 seconds
        
        # Phase 1: Size Stability
        print(f"Verifying stability for: {os.path.basename(file_path)}")
        for i in range(150): # Max 30 seconds (150 * 0.2) wait for size to stabilize
            try:
                current_size = os.path.getsize(file_path)
            except FileNotFoundError:
                return False # File disappeared (e.g. renamed/deleted)
            
            # v1.8.7: Queue-Aware Batch Logic
            # If I am 0 bytes...
            if current_size == 0:
                # Check if my neighbors are busy (Batch Download in progress?)
                if self.is_folder_busy(file_path):
                    # Neighbors are active! I should wait my turn.
                    # Reset my wait counter so I don't timeout prematurely.
                    zero_byte_retries = 0 
                    stable_count = 0
                    time.sleep(check_interval)
                    continue

                # No neighbors are active. It's just me.
                # Use the Grace Period logic (v1.8.3)
                if zero_byte_retries < max_zero_byte_retries:
                    zero_byte_retries += 1
                    stable_count = 0
                    time.sleep(check_interval)
                    continue

            if current_size == last_size:
                stable_count += 1
            else:
                stable_count = 0 # Reset if size changed
                
            last_size = current_size
            
            if stable_count >= stability_checks:
                break # Stable!
            
            time.sleep(check_interval)
            
        if stable_count < stability_checks:
            print(f"Timeout waiting for size stability: {file_path}")
            return False

        # Phase 2: Lock Check (Rename Method)
        # Try to rename the file to ITSELF. Windows throws error if locked.
        print(f"Checking lock status for: {os.path.basename(file_path)}")
        for attempt in range(lock_retries):
            try:
                os.rename(file_path, file_path)
                return True # Success! File is free.
            except OSError:
                time.sleep(check_interval)
                pass # Retry
        
        print(f"File is locked by another process: {file_path}")
        return False

class FileWatcher:
    def __init__(self):
        self.observer = None
        from app.settings import SettingsManager
        self.settings_manager = SettingsManager()
        
        self.path_to_watch = self.settings_manager.get("watch_folder")
        if not self.path_to_watch or not os.path.exists(self.path_to_watch):
            self.path_to_watch = os.path.join(os.path.expanduser("~"), "Downloads")
        
        self.event_handler = DownloadHandler()

    def start(self):
        # Always reload path from settings to ensure we use the latest selection
        self.path_to_watch = self.settings_manager.get("watch_folder")
        if not self.path_to_watch or not os.path.exists(self.path_to_watch):
             # Fallback (Safety)
             self.path_to_watch = os.path.join(os.path.expanduser("~"), "Downloads")

        if not os.path.exists(self.path_to_watch):
            print(f"Watch directory {self.path_to_watch} does not exist.")
            return
            
        if self.observer:
            if self.observer.is_alive():
                print("Observer already running.")
                return
            else:
                self.observer = None

        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.path_to_watch, recursive=False)
        self.observer.start()
        print(f"Monitoring started on {self.path_to_watch}")

    def update_path(self, new_path):
        if not os.path.exists(new_path):
            return
        
        self.stop()
        
        self.path_to_watch = new_path
        self.start()
        print(f"Monitoring updated to {self.path_to_watch}")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("Monitoring stopped.")
