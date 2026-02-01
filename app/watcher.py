import time
import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.organizer import Organizer

class DownloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.organizer = Organizer()

    def on_created(self, event):
        if event.is_directory:
            return
        self.process(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        # When browser finishes download (rename .crdownload -> .zip), it triggers on_moved
        self.process(event.dest_path)

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

    def wait_for_file_ready(self, file_path, check_interval=1.0, stability_checks=3, lock_retries=10):
        """
        Ensures file is ready by:
        1. Checking size stability (no changes for 'stability_checks' intervals).
        2. Checking file lock (can we rename it?).
        """
        last_size = -1
        stable_count = 0
        
        # Phase 1: Size Stability
        print(f"Verifying stability for: {os.path.basename(file_path)}")
        for _ in range(60): # Max 60 seconds wait for size to stabilize
            try:
                current_size = os.path.getsize(file_path)
            except FileNotFoundError:
                return False # File disappeared (e.g. renamed/deleted)
            
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
