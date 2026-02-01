import os
import shutil
import time
from app.context import ContextManager
import re
import zipfile

class Organizer:
    def __init__(self):
        self.context_manager = ContextManager()
        self.on_success_callback = None

    def set_callback(self, callback):
        self.on_success_callback = callback


    def organize_file(self, file_path):
        """
        Move the file to the appropriate folder based on current context.
        """
        # Get current context
        context = self.context_manager.get_context()
        if not context:
            print(f"Skipping {file_path}: No active PLM context.")
            return

        # Use the ALREADY pre-calculated folder name from the context
        folder_name = context.get('folder_name')
        if not folder_name:
            print(f"Skipping {file_path}: No valid folder name determined.")
            return
            
        # Target Directory
        base_dir = os.path.dirname(file_path)
        target_dir = os.path.join(base_dir, folder_name)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Created directory: {target_dir}")
            
        filename = os.path.basename(file_path)
        destination = os.path.join(target_dir, filename)
        
        # Handle duplicate filename
        if os.path.exists(destination):
            base, ext = os.path.splitext(filename)
            timestamp = int(time.time())
            destination = os.path.join(target_dir, f"{base}_{timestamp}{ext}")

        # Retry logic for file locking issues (common in Windows)
        max_retries = 5
        moved_file = None
        for attempt in range(max_retries):
            try:
                shutil.move(file_path, destination)
                print(f"Moved {file_path} -> {destination}")
                moved_file = destination
                break
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f"File locked, retrying in 1s... ({file_path})")
                    time.sleep(1)
                else:
                    print(f"Failed to move file after {max_retries} attempts: {file_path}")
                    return None
            except Exception as e:
                print(f"Error moving file: {e}")
                return None

        if moved_file:
            # Check for Auto-Unzip
            if moved_file.lower().endswith('.zip'):
                print(f"ZIP detected! Starting background extraction: {moved_file}")
                import threading
                # Feature: Async Unzip
                # Hand off the heavy lifting to a background thread so the main watcher 
                # can go back to processing the next file immediately.
                threading.Thread(target=self.unzip_file, args=(moved_file,), daemon=True).start()

            if self.on_success_callback:
                self.on_success_callback(moved_file)
            
            return moved_file

    def unzip_file(self, zip_path):
        """
        Extracts zip file to a subfolder of the same name.
        """
        try:
            target_dir = os.path.dirname(zip_path)
            # Create extraction folder (e.g., source.zip -> source/)
            zip_name = os.path.basename(zip_path)
            folder_name = os.path.splitext(zip_name)[0]
            extract_to = os.path.join(target_dir, folder_name)

            if not os.path.exists(extract_to):
                os.makedirs(extract_to)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                print(f"Extracted {zip_name} to {extract_to}")
            
            return True
        except Exception as e:
            print(f"Error unzipping {zip_path}: {e}")
            return False
