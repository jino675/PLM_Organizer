import json
import os

SETTINGS_FILE = "settings.json"

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def load(self):
        # 1. Initialize empty (Rely on settings.default.json)
        self.defaults = {}
        self.data = {}

        # 2. Load Template (settings.default.json) - Absolute Path
        base_dir = os.path.dirname(os.path.dirname(__file__))
        default_file = os.path.join(base_dir, "settings.default.json")
        
        if os.path.exists(default_file):
            try:
                with open(default_file, 'r') as f:
                    self.data.update(json.load(f))
            except Exception as e:
                print(f"Error loading defaults: {e}")

        # 3. Load User Settings (settings.json) - Relative Path (CWD)
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    self.data.update(json.load(f))
            except Exception as e:
                print(f"Error loading settings: {e}")

        # 4. Dynamic Defaults removed. 
        # Application now handles empty paths gracefully by requiring user setup.

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
