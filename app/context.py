from threading import Lock
import time

class ContextManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ContextManager, cls).__new__(cls)
                    cls._instance.current_data = {}
                    cls._instance.observers = []
                    cls._instance.last_heartbeat = 0
        return cls._instance

    def update_context(self, data):
        """
        Update the current PLM context (metadata).
        data: dict containing 'defect_id', 'plm_id', 'title'
        """
        import re
        with self._lock:
            # 1. Determine ID part
            defect = data.get('defect_id', '')
            plm = data.get('plm_id', '')
            id_part = defect if defect else (plm if plm else "Unknown")
            
            # 2. Parse Title Robustly (All logic centralized here)
            raw_title = data.get('title', '')
            # Restore original characters from Ghost Bridge escaping before any processing
            clean_title = raw_title.replace("‖", "|").replace("⦘", "]").replace("⦗", "[").strip()
            
            if clean_title:
                # Step A: Exhaustively strip all leading metadata blocks like [...], (...), {...}
                # and their ENTIRE contents, along with any leading whitespace.
                while True:
                    found = False
                    clean_title = clean_title.lstrip()
                    if not clean_title: break
                    
                    if clean_title.startswith('['):
                        end_idx = clean_title.find(']')
                        if end_idx != -1:
                            clean_title = clean_title[end_idx+1:]
                            found = True
                    elif clean_title.startswith('('):
                        end_idx = clean_title.find(')')
                        if end_idx != -1:
                            clean_title = clean_title[end_idx+1:]
                            found = True
                    elif clean_title.startswith('{'):
                        end_idx = clean_title.find('}')
                        if end_idx != -1:
                            clean_title = clean_title[end_idx+1:]
                            found = True
                    
                    if not found: break
                
                # Step B: Double check the stop at double space rule
                if "  " in clean_title:
                    clean_title = clean_title.split("  ")[0]
                
                # Step B-2 (v1.8.4): Sanitize Forbidden Windows Characters
                # Replace < > : " / \ | ? * with '#' (User preference)
                # Note: We do this BEFORE whitespace normalization so they stand out.
                clean_title = re.sub(r'[<>:"/\\|?*]', '#', clean_title)

                # Step C: Final trimming and Regex-based whitespace normalization
                clean_title = re.sub(r'\s+', '_', clean_title.strip())
                
                # Step D: Enforce 40-character limit
                if len(clean_title) > 40:
                    clean_title = clean_title[:38] + "__"
            
            if not clean_title:
                clean_title = "Untitled"
            
            if not clean_title:
                clean_title = "Untitled"
                
            # 3. Finalize Folder Name
            data['folder_name'] = f"[{id_part}]_{clean_title}"
            
            self.current_data = data
            self.last_heartbeat = time.time()
            self.notify_observers()

    def get_context(self):
        with self._lock:
            return self.current_data.copy()

    def add_observer(self, callback):
        self.observers.append(callback)

    def notify_observers(self):
        for callback in self.observers:
            try:
                callback(self.current_data)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def clear(self):
        """Resets the context to empty state."""
        with self._lock:
            # Only notify if there WAS data to clear to avoid spamming
            if self.current_data:
                self.current_data = {}
                self.last_heartbeat = time.time()
                self.notify_observers()
