from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QHBoxLayout, QStatusBar, QFileDialog, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, pyqtSignal
from app.context import ContextManager
from app.settings import SettingsManager
import datetime
import os

class LogStream:
    def __init__(self, signal):
        self.signal = signal
    def write(self, text):
        if text.strip():
            self.signal.emit(text.strip())
    def flush(self):
        pass

class MainWindow(QMainWindow):
    # Signals to bridge background thread -> UI thread
    context_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)

    def __init__(self, watcher, port=5555):
        super().__init__()
        self.watcher = watcher
        self.port = port
        self.settings_manager = SettingsManager()
        self.overlay = ContextOverlay(self.log_message)
        
        # Initial Always on Top state
        if self.settings_manager.get("always_on_top"):
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Connect signal to slot (UI Thread)
        self.context_signal.connect(self.update_status_display)
        
        # Add thread-safe observer
        # The context_manager is no longer directly managed by MainWindow,
        # assuming it's handled externally or through the watcher.
        # self.context_manager.add_observer(self.on_context_received) # Removed as per diff
        
        self.init_ui()
        
        # Connect Organizer Callback
        if hasattr(self.watcher, 'event_handler'):
            self.watcher.event_handler.organizer.set_callback(self.on_file_processed)
            
        # Initialize Overlay with Logger
        # Overlay initialization moved up and simplified
        if self.settings_manager.get("show_overlay"):
            self.overlay.show()
        else:
            self.overlay.hide()
            
    def on_context_received(self, data):
        # This runs on the Flask Thread.
        # Emit signal to transfer control to UI Thread.
        self.context_signal.emit(data)

    def init_ui(self):
        self.setWindowTitle("PLM Organizer") # Removed port from title
        self.setGeometry(100, 100, 600, 500)
        
        # Apply Dark Theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #555;
                margin-top: 20px;
                font-weight: bold;
                color: #aaa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
                color: #fff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border: 1px solid #777;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:disabled {
                background-color: #121212;
                color: #444;
                border: 1px solid #222;
                font-style: italic;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #333;
                color: #eee;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QLabel {
                color: #ddd;
            }
            QStatusBar {
                background-color: #1e1e1e;
                color: #aaa;
            }
        """)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # Corrected layout initialization
        
        # 1. Header (Centered)
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 10, 0, 10)
        
        self.title_label = QLabel("PLM Organizer")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.credits_label = QLabel("Created by jino.ryu")
        self.credits_label.setStyleSheet("color: #777; font-style: italic; font-size: 12px;")
        self.credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.credits_label)
        main_layout.addWidget(header_widget) # Used main_layout

        # 2. Settings Section
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        # Port Info
        port_label = QLabel(f"📡 Server Port: {self.port}")
        port_label.setStyleSheet("color: #90A4AE; font-weight: bold; margin-bottom: 5px;")
        settings_layout.addWidget(port_label)
        
        # Checkboxes Layout
        cb_layout = QHBoxLayout()
        self.overlay_cb = QCheckBox("Show Overlay")
        self.overlay_cb.setChecked(self.settings_manager.get("show_overlay"))
        self.overlay_cb.toggled.connect(self.toggle_overlay)
        
        self.always_top_cb = QCheckBox("Always on Top")
        self.always_top_cb.setChecked(self.settings_manager.get("always_on_top"))
        self.always_top_cb.toggled.connect(self.toggle_always_on_top)
        
        cb_layout.addWidget(self.overlay_cb)
        cb_layout.addWidget(self.always_top_cb)
        settings_layout.addLayout(cb_layout)
        
        # Target Folder Selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel(f"Target: {self.settings_manager.get('target_folder')}")
        self.folder_label.setStyleSheet("font-weight: bold; color: #4CAF50;") 
        self.change_folder_btn = QPushButton("Change Folder")
        self.change_folder_btn.clicked.connect(self.change_folder)
        
        folder_layout.addWidget(self.folder_label, 1)
        folder_layout.addWidget(self.change_folder_btn)
        settings_layout.addLayout(folder_layout)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group) # Used main_layout
        
        # 3. Control Button (Outside and Below Settings)
        self.toggle_btn = QPushButton("Stop Monitoring")
        self.toggle_btn.clicked.connect(self.toggle_monitoring)
        self.toggle_btn.setStyleSheet("background-color: #C62828; color: #ffffff; border: 1px solid #EF5350; padding: 12px; font-size: 15px;")
        main_layout.addWidget(self.toggle_btn) # Used main_layout

        # Current Context Display
        context_layout = QVBoxLayout()
        self.status_label = QLabel("Current Context: None")
        self.status_label.setStyleSheet("background-color: #333; color: #aaa; padding: 10px; border-radius: 5px; border: 1px solid #555;")
        self.status_label.setWordWrap(True)
        context_layout.addWidget(self.status_label)
        
        # Lock Status Indicator
        main_layout.addLayout(context_layout) # Used main_layout

        # Logs
        main_layout.addWidget(QLabel("Logs:")) # Used main_layout
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area) # Used main_layout

        # Connect log signal to log area
        self.log_signal.connect(self.log_area.append)

        # Redirect stdout/stderr to GUI
        import sys
        sys.stdout = LogStream(self.log_signal)
        sys.stderr = LogStream(self.log_signal)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Monitoring Active")
        
        self.log_message("Application Started")
        
        # State
        self.monitoring_active = True
        self.change_folder_btn.setEnabled(False) 

    @pyqtSlot(dict)
    def update_status_display(self, data):
        defect = data.get('defect_id', '')
        plm_id = data.get('plm_id', '')
        title = data.get('title', '')
        url = data.get('url', 'Unknown Source')

        # Always log that SOMETHING was received
        id_display = defect if defect else (plm_id if plm_id else "No ID")
        self.log_message(f"Update: {id_display} | {title if title else 'No Title'} ({url})")
        
        # 1. Handle Empty Context (Non-PLM page or no data)
        if not defect and not plm_id and not title:
            # Revert to Ready state
            self.current_folder_name = None
            display_text = "📂 Ready (Waiting for Data...)"
            self.status_label.setText(display_text)
            self.status_label.setStyleSheet("background-color: #37474F; color: #90A4AE; padding: 15px; border-radius: 8px; border: 1px solid #455A64; font-size: 14px; font-weight: bold;")
            self.overlay.update_text(display_text)
            return

        # 2. Calculate Preview Name
        id_part = ""
        if defect:
            id_part = defect
        elif plm_id:
            id_part = plm_id
        else:
            id_part = "Unknown"
        
        clean_title = title
        if clean_title:
             while clean_title.strip().startswith('['):
                 end = clean_title.find(']')
                 if end != -1:
                     clean_title = clean_title[end+1:].strip()
                 else:
                     break
             if "  " in clean_title:
                 clean_title = clean_title.split("  ")[0]
             clean_title = clean_title.replace(" ", "_")
        else:
            clean_title = "Untitled"
            
        folder_name = f"[{id_part}]_{clean_title}"
        self.current_folder_name = folder_name 
        
        # Update Display (Unified Format)
        display_text = f"📂 Target: {folder_name}"
        if len(display_text) > 150:
            display_text = display_text[:147] + "..."
            
        self.status_label.setText(display_text)
        self.status_label.setStyleSheet("background-color: #0D47A1; color: white; padding: 15px; border-radius: 8px; border: 1px solid #42A5F5; font-size: 14px; font-weight: bold;")
 
        # Update Overlay (Sync)
        self.overlay.update_text(display_text)

    def on_file_processed(self, dest_path):
        folder_name = os.path.basename(os.path.dirname(dest_path))
        file_name = os.path.basename(dest_path)
        self.log_message(f"✅ Moved: {file_name} -> 📂 {folder_name}")

    def toggle_monitoring(self):
        if self.monitoring_active:
            self.watcher.stop()
            self.monitoring_active = False
            self.toggle_btn.setText("Start Monitoring")
            self.toggle_btn.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; border: 1px solid #4CAF50;")
            self.statusBar().showMessage("Monitoring Paused")
            self.log_message("Monitoring Paused")
            self.change_folder_btn.setEnabled(True)
        else:
            self.watcher.start()
            self.monitoring_active = True
            self.toggle_btn.setText("Stop Monitoring")
            self.toggle_btn.setStyleSheet("background-color: #C62828; color: #ffffff; border: 1px solid #EF5350;")
            self.statusBar().showMessage("Monitoring Active")
            self.log_message("Monitoring Resumed")
            self.change_folder_btn.setEnabled(False)

    def toggle_overlay(self, checked):
        self.settings_manager.set("show_overlay", checked)
        if not checked:
            self.overlay.hide()
        else:
            self.overlay.show()
            self.overlay.reposition()

    def toggle_always_on_top(self, checked):
        self.settings_manager.set("always_on_top", checked)
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show() # Required to apply flags

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder")
        if folder:
            self.settings_manager.set("target_folder", folder)
            self.settings_manager.set("watch_folder", folder) 
            
            self.folder_label.setText(f"Target Folder: {folder}")
            self.log_message(f"Target folder changed to: {folder}")
            
            if self.monitoring_active:
                self.watcher.update_path(folder)

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}") 

class ContextOverlay(QWidget):
    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger
        self.settings_manager = SettingsManager()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # STRICT FIXED SIZE
        self.FIXED_WIDTH = 350
        self.FIXED_HEIGHT = 32 
        self.setFixedSize(self.FIXED_WIDTH, self.FIXED_HEIGHT)
        
        self.display_text = "Waiting..."
        self._dragging = False
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self.snap_to_corner()
            event.accept()

    def snap_to_corner(self):
        """Finds the nearest corner of the current monitor and snaps to it."""
        screen = self.screen().availableGeometry()
        center = self.geometry().center()
        
        # Calculate distances to 4 corners
        corners = {
            "top-left": (screen.left() + 30, screen.top() + 30),
            "top-right": (screen.right() - self.FIXED_WIDTH - 30, screen.top() + 30),
            "bottom-left": (screen.left() + 30, screen.bottom() - self.FIXED_HEIGHT - 30),
            "bottom-right": (screen.right() - self.FIXED_WIDTH - 30, screen.bottom() - self.FIXED_HEIGHT - 30)
        }
        
        nearest_anchor = "bottom-right"
        min_dist = float('inf')
        
        for anchor, (x, y) in corners.items():
            dist = (center.x() - (x + self.FIXED_WIDTH/2))**2 + (center.y() - (y + self.FIXED_HEIGHT/2))**2
            if dist < min_dist:
                min_dist = dist
                nearest_anchor = anchor
        
        # Save and Apply
        self.settings_manager.set("overlay_anchor", nearest_anchor)
        self.reposition()

    def reposition(self):
        """Positions the widget based on the saved anchor in settings."""
        screen = self.screen().availableGeometry()
        anchor = self.settings_manager.get("overlay_anchor", "bottom-right")
        
        margin = 30
        if anchor == "top-left":
            x, y = screen.left() + margin, screen.top() + margin
        elif anchor == "top-right":
            x, y = screen.right() - self.FIXED_WIDTH - margin, screen.top() + margin
        elif anchor == "bottom-left":
            x, y = screen.left() + margin, screen.bottom() - self.FIXED_HEIGHT - margin
        else: # bottom-right
            x, y = screen.right() - self.FIXED_WIDTH - margin, screen.bottom() - self.FIXED_HEIGHT - margin
            
        self.move(x, y)
        self.log(f"Snapped to {anchor} at ({x}, {y})")

    def showEvent(self, event):
        self.reposition()
        super().showEvent(event)
        
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QFont, QBrush, QPen, QFontMetrics
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Draw Background
        rect = self.rect().adjusted(2, 2, -2, -2)
        bg_color = QColor(30, 30, 30, 230)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 8, 8)
        
        # 2. Draw Text
        painter.setPen(QColor("#66BB6A"))
        font = QFont("Segoe UI", 11)
        font.setBold(True)
        painter.setFont(font)
        
        metrics = QFontMetrics(font)
        elided_text = metrics.elidedText(self.display_text, Qt.TextElideMode.ElideRight, rect.width() - 20)
        
        text_rect = rect.adjusted(10, 0, -10, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_text)
        
        # 3. Border
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRoundedRect(rect, 8, 8)

    def update_text(self, text):
        if self.display_text == text:
            return
        self.display_text = text
        self.update()
        if not self.isVisible():
            self.show()
            self.reposition()

    def log(self, msg):
        if self.logger:
            self.logger(f"[Overlay] {msg}")
