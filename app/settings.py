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
            "overlay_anchor": "bottom-right",
            "window_geometry": [100, 100, 450, 700] # Clean Default
        }
        
        # v1.8.13: Load template defaults if available
        default_file = "settings.default.json"
        if os.path.exists(default_file):
            try:
                with open(default_file, 'r') as f:
                    template_defaults = json.load(f)
                    self.defaults.update(template_defaults)
            except Exception as e:
                print(f"Error loading template defaults: {e}")

        self.data = self.defaults.copy()

        # v1.8.13: Load template defaults if available
        # Fix: Use absolute path (relative to app/settings.py -> root)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        default_file = os.path.join(base_dir, "settings.default.json")
        
        if os.path.exists(default_file):
            try:
                with open(default_file, 'r') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"Error loading default settings: {e}")

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
