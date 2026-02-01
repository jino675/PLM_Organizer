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
        self.defaults = {
            "target_folder": os.path.join(os.path.expanduser("~"), "Downloads", "MyPLM"),
            "watch_folder": os.path.join(os.path.expanduser("~"), "Downloads"),
            "show_overlay": True,
            "always_on_top": False,
            "auto_unzip": True,
            "overlay_anchor": "bottom-right" # bottom-right, bottom-left, top-right, top-left
        }
        self.data = self.defaults.copy()

        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"Error loading settings: {e}")

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
