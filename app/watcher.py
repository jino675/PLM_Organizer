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
                # Small delay to ensure file is written
                time.sleep(0.5)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    from app.context import ContextManager
                    ContextManager().update_context(data)
                
                # Instantly delete to keep the folder clean
                os.remove(file_path)
                print("Ninja Mode: Context updated and bridge file deleted.")
            except Exception as e:
                print(f"Ninja Mode Error: {e}")
            return

        # 2. Ignore other temporary download files
        if filename.endswith('.crdownload') or filename.endswith('.tmp') or filename.endswith('.download'):
            return
        
        # 3. Regular File Processing
        print(f"New file detected: {file_path}")
        # Small delay to ensure handle release?
        time.sleep(1)
        self.organizer.organize_file(file_path)

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
