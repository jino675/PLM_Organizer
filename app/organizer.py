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


    def sanitize_filename(self, name):
        # Remove characters invalid for Windows filenames
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def organize_file(self, file_path):
        """
        Move the file to the appropriate folder based on current context.
        """
        # Get current context
        context = self.context_manager.get_context()
        if not context:
            print(f"Skipping {file_path}: No active PLM context.")
            return

        defect_id = context.get('defect_id')
        plm_id = context.get('plm_id')
        title = context.get('title')

        # Strictly check for valid context
        if not defect_id and not plm_id:
            print(f"Skipping {file_path}: No valid ID context (Defect or PLM ID missing).")
            return

        # Determine Folder Name
        id_part = defect_id if defect_id else plm_id
            
        # Clean title: Remove leading brackets, spaces, etc if needed.
        # User requirement: [DefectID]_Title
        # "Title" needs parsing: "remove leading brackets and spaces, replace middle spaces with underscore, stop at double space"
        
        clean_title = self.parse_title(title)
        
        folder_name_str = f"[{id_part}]_{clean_title}"
        folder_name = self.sanitize_filename(folder_name_str)
        
        # Target Directory
        # Use parent directory of the file (which is the Watch Folder)
        # Verify if we should use a fixed target from settings?
        # For now, sticking to relative subfolder in the watch directory.
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
                print(f"ZIP detected! Starting extraction: {moved_file}")
                self.unzip_file(moved_file)

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

    def parse_title(self, raw_title):
        """
        Parses the PLM Title based on rules:
        - Remove ALL leading metadata blocks like [...], (...), {...} and spaces.
        - Replace internal spaces with underscore.
        - Stop at double space.
        - Limit to 40 characters.
        """
        if not raw_title:
            return "Untitled"
            
        current = raw_title.strip()
        
        # 1. Remove all leading brackets [], (), {} and surrounding whitespace
        while True:
            found_bracket = False
            # Square Brackets
            if current.startswith('[') and ']' in current:
                idx = current.find(']')
                current = current[idx+1:].strip()
                found_bracket = True
            # Parentheses
            elif current.startswith('(') and ')' in current:
                idx = current.find(')')
                current = current[idx+1:].strip()
                found_bracket = True
            # Curly Braces
            elif current.startswith('{') and '}' in current:
                idx = current.find('}')
                current = current[idx+1:].strip()
                found_bracket = True
            
            if not found_bracket:
                break
        
        # 2. Stop at double space (common separator in PLM titles)
        double_space_index = current.find("  ")
        if double_space_index != -1:
            current = current[:double_space_index]
            
        # 3. Final trim and internal space replacement
        current = current.strip()
        current = current.replace(" ", "_")
        
        # 4. Limit length to 40 characters
        if len(current) > 40:
            current = current[:37] + "..."
            
        return current if current else "Untitled"
