import os
import shutil
import time
import threading
import subprocess
from app.context import ContextManager
import re
import zipfile

# ... (Previous code remains the same until process_zip_workflow)

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

        # Priority 1: Windows 'tar' (Robust for Long Paths)
        # User requested this as default for modern Windows env.
        if self.unzip_with_tar(zip_path, extract_path):
             unzip_success = True
             print(f"Unzip successful (System Tar): {zip_name}")
        else:
             # Priority 2: Python 'zipfile' (Fallback/Legacy)
             print("System Tar failed/missing. Falling back to Python zipfile...")
             try:
                # Verification delay
                time.sleep(0.5)

                if not os.path.exists(zip_path):
                    print(f"Error: ZIP file missing before unzip: {zip_path}")
                elif not zipfile.is_zipfile(zip_path):
                    print(f"Error: Invalid or Corrupt ZIP file: {zip_path}")
                else:
                    if not os.path.exists(extract_path):
                        os.makedirs(extract_path)

                    print(f"Extracting {zip_name} to {extract_path} (Legacy Mode)...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    unzip_success = True
                    print("Unzip successful (Legacy Mode).")

             except zipfile.BadZipFile:
                print(f"Error: Bad ZIP File (Corrupt): {zip_path}")
             except PermissionError:
                print(f"Error: Permission Denied during Unzip (Locked): {zip_path}")
             except Exception as e:
                print(f"Error in ZIP workflow (Unzip Step): {e}")

        # B. Move Original ZIP (ALWAYS move)
        print(f"Moving ZIP to {target_dir}...")
        moved_zip = self.move_file_safe(zip_path, target_dir)

        # C. Move Extracted Folder (Only if unzip succeeded)
        if os.path.exists(extract_path):
            if unzip_success:
                 print(f"Moving Extracted Folder to {target_dir}...")
                 self.move_file_safe(extract_path, target_dir)
            else:
                 print(f"Moving Partial/Failed Extracted Folder to {target_dir}...")
                 self.move_file_safe(extract_path, target_dir)
        
        if self.on_success_callback and moved_zip:
            self.on_success_callback(moved_zip)

    def unzip_with_tar(self, zip_path, extract_path):
        """
        Primary unzip using Windows 10+ built-in 'tar.exe'.
        Solves MAX_PATH (260 char) issues.
        """
        try:
            # Check if tar exists (Fast check)
            if not shutil.which("tar"):
                return False
            
            # tar -xf "source.zip" -C "destination_folder"
            if not os.path.exists(extract_path):
                os.makedirs(extract_path)
                
            result = subprocess.run(
                ['tar', '-xf', zip_path, '-C', extract_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"Tar Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Tar Unexpected Error: {e}")
            return False

    def move_file_safe(self, source, target_folder):
        # ... (Rest of code stays same)

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
