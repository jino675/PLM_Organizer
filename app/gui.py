from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QHBoxLayout, QStatusBar, QFileDialog, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPainter, QColor, QFont, QBrush, QPen, QFontMetrics
from app.context import ContextManager
from app.settings import SettingsManager
import datetime
import time
import os
import win32gui
import win32con

class LogStream:
    def __init__(self, signal):
        self.signal = signal
        self._lock = False # Recursion protection

    def write(self, text):
        if self._lock: return
        try:
            self._lock = True
            if text.strip():
                self.signal.emit(text.strip())
        finally:
            self._lock = False

    def flush(self):
        pass

class MainWindow(QMainWindow):
    # Signals to bridge background thread -> UI thread
    context_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)

    def __init__(self, watcher):
        super().__init__()
        self.watcher = watcher
        
        # Load Config
        self.settings_manager = SettingsManager()
        self.context_manager = ContextManager()
        self.dot_count = 0  # Animation counter
        
        # Connect signals
        self.context_signal.connect(self.update_status_display)
        self.log_signal.connect(self._log_to_area) # Safe wrapper
        
        # Add observer to singleton ContextManager
        self.context_manager.add_observer(self.on_context_received)
        
        # Initialize Overlay (Don't show yet)
        self.overlay = ContextOverlay(self.log_message_signal)
        
        self.init_ui()
        
        if hasattr(self.watcher, 'event_handler'):
            self.watcher.event_handler.organizer.set_callback(self.on_file_processed)
            
        # Defer showing the overlay to ensure everything is initialized
        QTimer.singleShot(500, self.delayed_setup)
        
        # Status Bar Timer (Health Check & Animation)
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.update_health_status)
        self.health_timer.start(1000) # Every 1 second for smoother animation

    def delayed_setup(self):
        # Apply Always on Top if needed
        if self.settings_manager.get("always_on_top"):
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            
        if self.settings_manager.get("show_overlay"):
            self.overlay.show()
            self.overlay.reposition()

    def on_context_received(self, data):
        self.context_signal.emit(data)

    def _log_to_area(self, msg):
        if hasattr(self, 'log_area'):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_area.append(f"[{timestamp}] {msg}")

    def init_ui(self):
        self.setWindowTitle("PLM Organizer") 
        self.setGeometry(100, 100, 600, 500)
        
        # Set App Icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
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
                border-radius: 8px; /* Strict 8px */
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
                border: none; /* Border handled by GroupBox */
                color: #eee;
                font-family: Consolas, monospace;
                font-size: 12px;
                border-radius: 8px;
            }
            QLabel {
                color: #ddd;
            }
            QStatusBar {
                background-color: #1e1e1e;
                color: #aaa;
            }
            /* Scrollbar Styling */
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) 
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # FIX: Keep content top-aligned but allow spacing
        
        # 1. Header (Title - Version)
        header_widget = QWidget()
        header_vbox = QVBoxLayout(header_widget)
        header_vbox.setContentsMargins(10, 15, 10, 5)
        
        # Load Version (Moved up to use in Title Row)
        version_str = "Unknown"
        version_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
        if os.path.exists(version_path):
            try:
                with open(version_path, "r") as f:
                    version_str = f.read().strip()
            except: pass

        title_row = QWidget()
        title_row_layout = QHBoxLayout(title_row)
        title_row_layout.setContentsMargins(0, 0, 0, 0)
        
        # BALANCING TRICK: Left Spacer Widget (Matches Version Width)
        # This ensures the middle stretch pushes against equal sides, keeping Title perfectly centered.
        balancer = QLabel()
        balancer.setFixedWidth(60) 
        title_row_layout.addWidget(balancer)
        
        title_row_layout.addStretch(1)
        
        self.title_label = QLabel("PLM Organizer")
        self.title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff; letter-spacing: 2px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row_layout.addWidget(self.title_label)
        
        title_row_layout.addStretch(1)
        
        # Right: Version (v1.x.x)
        self.version_label = QLabel(f"v{version_str}")
        self.version_label.setFixedWidth(60)
        self.version_label.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 4px;")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        title_row_layout.addWidget(self.version_label)
        
        header_vbox.addWidget(title_row)
        
        # Row 2: Credits Only
        credits_row = QHBoxLayout()
        credits_row.addStretch(1)
        
        self.credits_label = QLabel("Created by jino.ryu")
        self.credits_label.setStyleSheet("color: #888; font-style: italic; font-size: 11px;")
        self.credits_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        credits_row.addWidget(self.credits_label)
        
        header_vbox.addLayout(credits_row)
        
        main_layout.addWidget(header_widget)

        # 2. Settings Section
        settings_group = QGroupBox("Settings")
        settings_group.setStyleSheet("""
            QGroupBox { 
                border: 1px solid #555; 
                border-radius: 8px; 
                margin-top: 20px; 
                padding-top: 15px; 
                font-weight: bold;
                color: #81C784; /* Green Title as requested */
                background-color: #2b2b2b;
            }
            QGroupBox::title {
                subcontrol-origin: border;
                subcontrol-position: top center;
                top: -10px;
                padding: 0 10px;
                background-color: #2b2b2b;
            }
        """)
        settings_layout = QVBoxLayout()
        
        # Checkboxes Layout
        cb_layout = QHBoxLayout()
        self.overlay_cb = QCheckBox("Show Overlay")
        self.overlay_cb.setChecked(self.settings_manager.get("show_overlay") if self.settings_manager.get("show_overlay") is not None else True)
        self.overlay_cb.toggled.connect(self.toggle_overlay)
        
        self.always_top_cb = QCheckBox("Always on Top")
        self.always_top_cb.setChecked(self.settings_manager.get("always_on_top") if self.settings_manager.get("always_on_top") is not None else False)
        self.always_top_cb.toggled.connect(self.toggle_always_on_top)
        
        cb_layout.addWidget(self.overlay_cb)
        cb_layout.addWidget(self.always_top_cb)
        settings_layout.addLayout(cb_layout)
        
        # Target Folder Styled Field
        folder_container = QWidget()
        folder_container_layout = QVBoxLayout(folder_container)
        folder_container_layout.setContentsMargins(0, 10, 0, 0)
        
        folder_label_title = QLabel("Watch Folder:")
        folder_label_title.setStyleSheet("color: #aaa; font-size: 12px;")
        folder_container_layout.addWidget(folder_label_title)

        folder_field_layout = QHBoxLayout()
        self.folder_display = QLabel(self.settings_manager.get('target_folder'))
        self.folder_display.setStyleSheet("""
            background-color: #1a1a1a; 
            color: #4CAF50; 
            padding: 8px; 
            border-radius: 8px; /* Unified Radius */
            border: 1px solid #333;
            font-family: 'Consolas', monospace;
            font-size: 12px;
        """)
        self.folder_display.setWordWrap(True)
        
        self.change_folder_btn = QPushButton("Change")
        self.change_folder_btn.setFixedWidth(80)
        self.change_folder_btn.clicked.connect(self.change_folder)
        
        folder_field_layout.addWidget(self.folder_display, 1)
        folder_field_layout.addWidget(self.change_folder_btn)
        folder_container_layout.addLayout(folder_field_layout)
        
        settings_layout.addWidget(folder_container)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 3. Control Button (Outside and Below Settings)
        self.toggle_btn = QPushButton("Stop Monitoring")
        self.toggle_btn.clicked.connect(self.toggle_monitoring)
        self.toggle_btn.setStyleSheet("background-color: #C62828; color: #ffffff; border: 1px solid #EF5350; padding: 12px; font-size: 15px; border-radius: 8px;") # Unified radius
        main_layout.addWidget(self.toggle_btn) 

        # Current Context Display
        context_layout = QVBoxLayout()
        self.status_label = QLabel("📁 Ready (Waiting for Data...)")
        self.status_label.setStyleSheet("background-color: #333; color: #aaa; padding: 10px; border-radius: 8px; border: 1px solid #555; font-weight: bold;") # Unified radius (8px)
        self.status_label.setWordWrap(True)
        context_layout.addWidget(self.status_label)
        
        main_layout.addLayout(context_layout) 

        # Logs - Now in a GroupBox with matching style!
        log_group = QGroupBox("Logs")
        log_group.setStyleSheet("""
            QGroupBox { 
                border: 1px solid #555; 
                border-radius: 8px; 
                margin-top: 10px; /* Slight adjust */
                padding-top: 15px; 
                font-weight: bold;
                color: #81C784; /* Green Title */
                background-color: #2b2b2b;
            }
            QGroupBox::title {
                subcontrol-origin: border;
                subcontrol-position: top center;
                top: -10px;
                padding: 0 10px;
                background-color: #2b2b2b;
            }
        """)
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(5, 10, 5, 5) 
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Connect log signal
        # Redirect stdout/stderr - using a safer way to avoid recursion if printing fails
        import sys
        self._stdout_old = sys.stdout
        self._stderr_old = sys.stderr
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
        
        # 1. Handle Empty context
        if not defect and not plm_id and not title:
            display_text = "📁 Ready (Waiting for Data...)"
            self.status_label.setText(display_text)
            self.status_label.setStyleSheet("background-color: #333; color: #aaa; padding: 10px; border-radius: 8px; border: 1px solid #555; font-weight: bold;")
            self.overlay.update_text(display_text)
            return

        # 2. Get Pre-calculated Folder Name
        folder_name = data.get('folder_name', 'Unknown')
        self.current_folder_name = folder_name 
        
        # Update Display (Unified Format)
        display_text = f"📂 Target: {folder_name}"
        if len(display_text) > 80:
            display_text = display_text[:77] + "..."
            
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
            self.toggle_btn.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; border: 1px solid #4CAF50; border-radius: 8px;")
            self.statusBar().showMessage("Monitoring Paused")
            self.log_message("Monitoring Paused")
            self.change_folder_btn.setEnabled(True)
        else:
            self.watcher.start()
            self.monitoring_active = True
            self.toggle_btn.setText("Stop Monitoring")
            self.toggle_btn.setStyleSheet("background-color: #C62828; color: #ffffff; border: 1px solid #EF5350; border-radius: 8px;")
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
        hwnd = int(self.winId())
        flag = win32con.HWND_TOPMOST if checked else win32con.HWND_NOTOPMOST
        # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE = 0x0002 | 0x0001 | 0x0010 = 19
        win32gui.SetWindowPos(hwnd, flag, 0, 0, 0, 0, 19)
        self.log_message(f"Always on Top: {'Enabled' if checked else 'Disabled'}")

    def update_health_status(self):
        """Update the status bar with extension connection health and animation."""
        if not hasattr(self, 'ghost_permanent_label'):
            # Add Ghost Info to permanent area (Right side)
            self.ghost_permanent_label = QLabel("👻 Using Ghost Bridge  ") # Added Emoji
            # Removed background color, kept text style only
            self.ghost_permanent_label.setStyleSheet("color: #90A4AE; font-weight: bold; font-family: 'Segoe UI'; font-size: 13px; background: transparent;") 
            self.statusBar().addPermanentWidget(self.ghost_permanent_label)

        last_time = self.context_manager.last_heartbeat
        if last_time == 0 or (time.time() - last_time) >= 15:
            # Waiting/Not Working -> Animated dots (Red)
            self.dot_count = (self.dot_count + 1) % 4
            dots = "." * self.dot_count
            status = f"Chrome Extension: Waiting{dots}"
            color = "#F44336; font-weight: bold;" # Red
        else:
            # Connected/Active -> Static (Green)
            status = "Chrome Extension: Active (Linked)"
            color = "#4CAF50; font-weight: bold;" # Green
        
        self.statusBar().showMessage(status)
        self.statusBar().setStyleSheet(f"QStatusBar {{ background-color: #1e1e1e; color: {color}; font-family: 'Segoe UI'; font-size: 13px; padding-left: 5px; }}")

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder")
        if folder:
            self.settings_manager.set("target_folder", folder)
            self.settings_manager.set("watch_folder", folder) 
            
            if hasattr(self, 'folder_display'):
                self.folder_display.setText(folder)
                
            self.log_message(f"Target folder changed to: {folder}")
            
            if self.monitoring_active:
                self.watcher.update_path(folder)

    def log_message(self, message):
        """Thread-safe logging by emitting a signal."""
        self.log_signal.emit(message)

    def log_message_signal(self, message):
        """Wrapper for overlay to use the signal."""
        self.log_signal.emit(message)

class SnapGuide(QWidget):
    """Tiny circular dot widget to show snap locations during drag."""
    def __init__(self, color="#81C784"):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(16, 16)
        self.color = color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(3, 3, 10, 10)

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
        
        # Set Icon for Overlay Taskbar entry
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.display_text = "Waiting..."
        self._dragging = False
        self._drag_pos = None
        
        # Snap Guides (Pre-create 4 dots)
        self.guides = [SnapGuide() for _ in range(4)]

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.show_guides()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self.hide_guides()
            self.snap_to_corner()
            event.accept()

    def show_guides(self):
        """Shows 4 dots at screen corners."""
        screen = self.screen().availableGeometry()
        margin = 38 # Center of 16x16 dot at 30px margin offset
        points = [
            (screen.left() + margin - 8, screen.top() + margin - 8),
            (screen.right() - margin - 8, screen.top() + margin - 8),
            (screen.left() + margin - 8, screen.bottom() - margin - 8),
            (screen.right() - margin - 8, screen.bottom() - margin - 8)
        ]
        for i, (x, y) in enumerate(points):
            self.guides[i].move(x, y)
            self.guides[i].show()

    def hide_guides(self):
        for g in self.guides:
            g.hide()

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
        anchor = self.settings_manager.get("overlay_anchor")
        if not anchor:
            anchor = "bottom-right"
        
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
