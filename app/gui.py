from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QHBoxLayout, QStatusBar, QFileDialog, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, pyqtSignal
from app.context import ContextManager
from app.settings import SettingsManager
import datetime
import os

class MainWindow(QMainWindow):
    # Signal to bridge background thread -> UI thread
    context_signal = pyqtSignal(dict)

    def __init__(self, watcher):
        super().__init__()
        self.watcher = watcher
        self.context_manager = ContextManager()
        self.settings_manager = SettingsManager()
        
        # Connect signal to slot (UI Thread)
        self.context_signal.connect(self.update_status_display)
        
        # Add thread-safe observer
        self.context_manager.add_observer(self.on_context_received)
        
        self.init_ui()
        
        # Setup Smart Lock
        self.lock_timer = QTimer()
        self.lock_timer.setSingleShot(True)
        self.lock_timer.timeout.connect(self.unlock_context)
        self.context_locked = False
        
        # Connect Organizer Callback
        if hasattr(self.watcher, 'event_handler'):
            self.watcher.event_handler.organizer.set_callback(self.on_file_processed)
            
        # Initialize Overlay with Logger
        self.overlay = ContextOverlay(logger=self.log_message)
        if self.settings_manager.get("show_overlay"):
            self.overlay.show()
        else:
            self.overlay.hide()
            
    def on_context_received(self, data):
        # This runs on the Flask Thread.
        # Emit signal to transfer control to UI Thread.
        self.context_signal.emit(data)

    def init_ui(self):
        self.setWindowTitle("PLM Organizer")
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
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Header / Credits
        header_layout = QHBoxLayout()
        title = QLabel("PLM Organizer")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        credits = QLabel("Created by jino.ryu")
        credits.setStyleSheet("color: gray; font-style: italic;")
        credits.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(credits)
        layout.addLayout(header_layout)

        # Settings Section
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        # Overlay Toggle
        self.overlay_cb = QCheckBox("Show Desktop Overlay (Bottom-Right)")
        self.overlay_cb.setChecked(self.settings_manager.get("show_overlay"))
        self.overlay_cb.toggled.connect(self.toggle_overlay)
        settings_layout.addWidget(self.overlay_cb)
        
        # Target Folder Selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel(f"Target Folder: {self.settings_manager.get('target_folder')}")
        self.folder_label.setStyleSheet("font-weight: bold; color: #4CAF50;") 
        self.change_folder_btn = QPushButton("Change Folder")
        self.change_folder_btn.clicked.connect(self.change_folder)
        
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.change_folder_btn)
        settings_layout.addLayout(folder_layout)
        
        # Control Buttons (Start/Stop)
        control_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("Stop Monitoring")
        self.toggle_btn.clicked.connect(self.toggle_monitoring)
        self.toggle_btn.setStyleSheet("background-color: #C62828; color: #ffffff; border: 1px solid #EF5350;")
        control_layout.addWidget(self.toggle_btn)
        
        settings_layout.addLayout(control_layout)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Current Context Display
        context_layout = QVBoxLayout()
        self.status_label = QLabel("Current Context: None")
        self.status_label.setStyleSheet("background-color: #333; color: #aaa; padding: 10px; border-radius: 5px; border: 1px solid #555;")
        self.status_label.setWordWrap(True)
        context_layout.addWidget(self.status_label)
        
        # Lock Status Indicator
        # Lock Status Indicator
        self.lock_indicator = QLabel("Ready (Waiting for Data...)")
        self.lock_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lock_indicator.setStyleSheet("color: green; font-size: 11px;")
        context_layout.addWidget(self.lock_indicator)
        
        layout.addLayout(context_layout)

        # Logs
        layout.addWidget(QLabel("Logs:"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Monitoring Active")
        
        self.log_message("Application Started")
        
        # State
        self.monitoring_active = True
        self.change_folder_btn.setEnabled(False) 

    @pyqtSlot(dict)
    def update_status_display(self, data):
        if self.context_locked:
            return
            
        defect = data.get('defect_id', '')
        plm_id = data.get('plm_id', '')
        title = data.get('title', '')
        
        # Calculate Preview Name
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
        self.status_label.setText(display_text)
        self.status_label.setStyleSheet("background-color: #0D47A1; color: white; padding: 15px; border-radius: 8px; border: 1px solid #42A5F5; font-size: 14px; font-weight: bold;")
 
        # Update Overlay (Sync)
        self.overlay.update_text(display_text)

    def on_file_processed(self, dest_path):
        self.lock_context(duration_sec=60)
        self.log_message(f"Processed: {os.path.basename(dest_path)}")

    def lock_context(self, duration_sec=60):
        self.context_locked = True
        self.lock_timer.start(duration_sec * 1000)
        
        folder = getattr(self, 'current_folder_name', 'Unknown')
        self.lock_indicator.setText(f"⏳ Processing... Locked to:\n{folder}\n({duration_sec}s remaining)")
        self.lock_indicator.setStyleSheet("color: #D32F2F; font-weight: bold; background-color: #FFEBEE; padding: 10px; border-radius: 5px; border: 1px solid #D32F2F;")
        self.log_message(f"Smart Lock Active ({duration_sec}s)")

    def unlock_context(self):
        self.context_locked = False
        self.lock_indicator.setText("✅ Ready (Waiting for files...)")
        self.lock_indicator.setStyleSheet("color: green; padding: 5px;")
        self.log_message("Smart Lock Released")
        
        data = self.context_manager.get_context()
        self.update_status_display(data)

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
        if checked:
            self.overlay.show()
            if hasattr(self, 'current_folder_name'):
                self.overlay.update_text(f"📂 Target: {self.current_folder_name}")
            else:
                self.overlay.update_text("Waiting...")
        else:
            self.overlay.hide()

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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # STRICT FIXED SIZE - NEVER CHANGES
        self.FIXED_WIDTH = 350
        self.FIXED_HEIGHT = 32 
        self.setFixedSize(self.FIXED_WIDTH, self.FIXED_HEIGHT)
        
        self.display_text = "Waiting..."
        
    def showEvent(self, event):
        self.reposition()
        super().showEvent(event)
        
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QFont, QBrush, QPen, QFontMetrics
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Draw Background (Semi-transparent Black/Grey)
        # Using a rect slightly smaller than widget size to allow for smooth borders
        rect = self.rect().adjusted(2, 2, -2, -2)
        
        bg_color = QColor(30, 30, 30, 230) # Dark Grey, High Opacity
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 8, 8) # Rounded corners
        
        # 2. Draw Text
        painter.setPen(QColor("#66BB6A")) # Green text
        font = QFont("Segoe UI", 11) # Slightly larger, readable font
        font.setBold(True)
        painter.setFont(font)
        
        # Elide Text (Truncate with ...) if it fits
        metrics = QFontMetrics(font)
        # 20px padding on sides
        elided_text = metrics.elidedText(self.display_text, Qt.TextElideMode.ElideRight, rect.width() - 20)
        
        # Center Vertically, Align Left with padding
        text_rect = rect.adjusted(10, 0, -10, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_text)
        
        # 3. Draw Border (Optional, for definition)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRoundedRect(rect, 8, 8)

    def update_text(self, text):
        if self.display_text == text:
            return

        self.display_text = text
        self.log(f"Updating text: {text}")
        
        # Force redraw - Geometry NEVER changes so no flicker
        self.update()
        
        if not self.isVisible():
            self.show()
            self.reposition() # Ensure it's in the right spot if it was hidden

    def reposition(self):
        screen = self.screen().availableGeometry()
        margin_right = 30
        margin_bottom = 30
        
        # Calculate Strict Position based on FIXED dimensions
        x = screen.width() - self.FIXED_WIDTH - margin_right
        y = screen.height() - self.FIXED_HEIGHT - margin_bottom
        
        self.log(f"Pos: ({x}, {y}) | Fixed Size: {self.FIXED_WIDTH}x{self.FIXED_HEIGHT}")
        self.move(x, y)

    def log(self, msg):
        if self.logger:
            self.logger(f"[Overlay] {msg}")
