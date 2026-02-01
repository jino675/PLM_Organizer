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
        Main entry point. Decides whether to just move or unzip-and-move.
        Running in a separate thread (spawned by Watcher).
        """
        # 1. Get Context
        context = self.context_manager.get_context()
        if not context:
            print(f"Skipping {file_path}: No active PLM context.")
            return

        folder_name = context.get('folder_name')
        if not folder_name:
            print(f"Skipping {file_path}: No valid folder name determined.")
            return
            
        # Target Directory
        base_dir = os.path.dirname(file_path)
        # Note: We move FROM base_dir TO target_dir
        # target_dir is usually different from base_dir (e.g. Downloads -> Documents/PLM/...)
        # But base_dir is where the file IS NOW (Downloads).
        
        # Construct absolute target path
        # Assuming the user wants to organize relative to the app or a fixed location?
        # Actually in v1 code, target_dir was os.path.join(base_dir, folder_name).
        # Meaning it creates a subfolder inside Downloads.
        target_dir = os.path.join(base_dir, folder_name)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Created directory: {target_dir}")

        # 2. Check Strategy
        filename = os.path.basename(file_path)
        is_zip = filename.lower().endswith('.zip')
        
        from app.settings import SettingsManager
        auto_unzip = SettingsManager().get("auto_unzip", True)

        if is_zip and auto_unzip:
            print(f"ZIP detected (Unzip-First Strategy): {file_path}")
            self.process_zip_workflow(file_path, target_dir)
        else:
            self.move_file_safe(file_path, target_dir)

    def process_zip_workflow(self, zip_path, target_dir):
        """
        Strategy v1.8.9:
        1. Unzip IN PLACE (Downloads folder)
        2. Move ZIP -> Target
        3. Move Extracted Folder -> Target
        """
        base_dir = os.path.dirname(zip_path)
        zip_name = os.path.basename(zip_path)
        folder_name = os.path.splitext(zip_name)[0]
        extract_path = os.path.join(base_dir, folder_name)

        # A. Unzip In-Place
        unzip_success = False
        try:
            # Verification delay (just in case)
            time.sleep(0.5)

            if not os.path.exists(zip_path):
                print(f"Error: ZIP file missing before unzip: {zip_path}")
                return

            if not zipfile.is_zipfile(zip_path):
                print(f"Error: Invalid or Corrupt ZIP file: {zip_path}")
                # We will still move it, but skip unzip
            else:
                if not os.path.exists(extract_path):
                    os.makedirs(extract_path)

                print(f"Extracting {zip_name} to {extract_path}...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                unzip_success = True
                print("Unzip successful.")

        except zipfile.BadZipFile:
            print(f"Error: Bad ZIP File (Corrupt): {zip_path}")
        except PermissionError:
            print(f"Error: Permission Denied during Unzip (Locked): {zip_path}")
        except Exception as e:
            print(f"Error in ZIP workflow (Unzip Step): {e}")

        # B. Move Original ZIP (ALWAYS move, even if unzip failed)
        print(f"Moving ZIP to {target_dir}...")
        moved_zip = self.move_file_safe(zip_path, target_dir)

        # C. Move Extracted Folder (Only if unzip succeeded/exists)
        if os.path.exists(extract_path) and unzip_success:
            print(f"Moving Extracted Folder to {target_dir}...")
            self.move_file_safe(extract_path, target_dir)
        elif os.path.exists(extract_path):
             # cleanup partial extraction if needed, or just move it too?
             # Better to move whatever we got.
             print(f"Moving Partial/Failed Extracted Folder to {target_dir}...")
             self.move_file_safe(extract_path, target_dir)
        
        if self.on_success_callback and moved_zip:
            self.on_success_callback(moved_zip)

    def move_file_safe(self, source, target_folder):
        """
        Moves a file OR directory to target_folder, handling duplicates.
        Returns the new path.
        """
        try:
            # v1.8.10: Check source existence to prevent race condition spam
            if not os.path.exists(source):
                print(f"Source not found (already moved?): {source}")
                return None

            name = os.path.basename(source)
            destination = os.path.join(target_folder, name)

            # Handle Duplicates
            if os.path.exists(destination):
                base, ext = os.path.splitext(name)
                timestamp = int(time.time())
                # If it's a folder, ext is empty.
                destination = os.path.join(target_folder, f"{base}_{timestamp}{ext}")

            # Retry Loop
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    shutil.move(source, destination)
                    print(f"Moved: {source} -> {destination}")
                    return destination
                except FileNotFoundError:
                    # Source disappeared during retry (Race condition resolved by other thread)
                    print(f"Source disappeared during move: {source}")
                    return None
                except PermissionError:
                    time.sleep(1)
                except Exception as e:
                    print(f"Move Error ({attempt}): {e}")
                    time.sleep(1)
            
            print(f"Failed to move {source} after retries.")
            return None
        except Exception as e:
            print(f"Critical Move Error: {e}")
            return None
