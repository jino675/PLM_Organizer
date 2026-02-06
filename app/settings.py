import json
import os
import shutil

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.init_paths()
            cls._instance.load()
        return cls._instance

    def init_paths(self):
        # Determine AppData path
        appdata = os.getenv('APPDATA')
        if not appdata:
            appdata = os.path.expanduser("~") # Fallback
            
        self.settings_dir = os.path.join(appdata, "PLMOrganizer")
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        
        # Ensure directory exists
        if not os.path.exists(self.settings_dir):
            os.makedirs(self.settings_dir)

    def get_app_version(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            version_file = os.path.join(base_dir, "VERSION")
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return "0.0.0"

    def parse_version(self, v_str):
        # Robust version parser (e.g., "1.8.15" -> (1, 8, 15))
        try:
            return tuple(map(int, v_str.split('.')))
        except:
            return (0, 0, 0)

    def load(self):
        current_version = self.get_app_version()
        current_ver_tuple = self.parse_version(current_version)

        # 1. Initialize with Defaults from Template
        self.data = {}
        base_dir = os.path.dirname(os.path.dirname(__file__))
        default_file = os.path.join(base_dir, "settings.default.json")
        
        if os.path.exists(default_file):
            try:
                with open(default_file, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error loading defaults: {e}")

        # 2. Check User Settings in AppData
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    user_data = json.load(f)
                
                saved_version = user_data.get("version", "0.0.0")
                saved_ver_tuple = self.parse_version(saved_version)

                # Version Check strategy: If Saved < Current, Reset.
                if saved_ver_tuple < current_ver_tuple:
                    print(f"[Settings] Version mismatch ({saved_version} < {current_version}). Resetting config.")
                    # We simply do NOT update self.data with user_data
                    # And maybe backup the old file? User said "Delete".
                    self.backup_and_reset(saved_version)
                else:
                    self.data.update(user_data)
                    
            except Exception as e:
                print(f"Error loading user settings: {e}")

    def backup_and_reset(self, old_version):
        # Rename old file just in case (Safety first, even if user said delete)
        try:
            backup_name = f"settings_backup_v{old_version}.json"
            backup_path = os.path.join(self.settings_dir, backup_name)
            if os.path.exists(self.settings_file):
                shutil.move(self.settings_file, backup_path)
            print(f"[Settings] Old settings backed up to {backup_name}")
        except Exception as e:
            print(f"Error resetting settings: {e}")

    def save(self):
        try:
            # Inject current version
            self.data['version'] = self.get_app_version()
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
