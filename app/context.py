from threading import Lock

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
        return cls._instance

    def update_context(self, data):
        """
        Update the current PLM context (metadata).
        data: dict containing 'defect_id', 'plm_id', 'title'
        """
        with self._lock:
            self.current_data = data
            print(f"Context Updated: {self.current_data}")
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
