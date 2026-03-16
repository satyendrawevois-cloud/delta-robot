import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from styles import ThemeManager
from serial_thread import SerialThread
from main_control import MainControlTab
from config import ConfigTab
from log import LogTab
from utils import format_goto_command, get_timestamp, format_gcode_buffer, count_points_in_buffer
from vision import VisionTab


class DeltaRobotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Delta Robot Controller v1.0 - WeVOIS Pro")
        self.setGeometry(100, 100, 1400, 800)
        
        # Current theme (default light)
        self.current_theme = "light"
        
        # Apply initial theme
        self.apply_theme("light")
        
        # Setup serial
        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.on_serial_data)
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.error_occurred.connect(self.on_serial_error)
        
        self.connected = False
        
        # Setup UI
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_central_widget()
        self.setup_status_bar()
        
        # Initialize logs
        QTimer.singleShot(500, lambda: self.add_log("INFO", "Delta Robot Controller v1.0 started"))
    
    def apply_theme(self, theme):
        """Apply theme to application"""
        if theme == "dark":
            self.setPalette(ThemeManager.get_dark_palette())
            self.setStyleSheet(ThemeManager.get_stylesheet("dark"))
            self.current_theme = "dark"
        else:
            self.setPalette(ThemeManager.get_light_palette())
            self.setStyleSheet(ThemeManager.get_stylesheet("light"))
            self.current_theme = "light"
        
        # Update theme button text
        if hasattr(self, 'theme_btn'):
            self.theme_btn.setText("🌙 Dark" if theme == "light" else "☀️ Light")
        
    def setup_menu_bar(self):
        """Setup menu bar with theme toggle"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        theme_action = QAction("Toggle Light/Dark Theme", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Setup main toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        # Theme toggle button
        self.theme_btn = QPushButton("🌙 Dark")
        self.theme_btn.setMaximumWidth(100)
        self.theme_btn.clicked.connect(self.toggle_theme)
        toolbar.addWidget(self.theme_btn)
        
        toolbar.addSeparator()
        
        # Emergency stop
        emergency_btn = QPushButton("⚠️ EMERGENCY STOP")
        emergency_btn.setObjectName("emergency")
        emergency_btn.setMinimumHeight(40)
        emergency_btn.clicked.connect(self.emergency_stop)
        toolbar.addWidget(emergency_btn)
    
    def setup_central_widget(self):
        """Setup main central widget with tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # Create tabs
        self.main_control = MainControlTab(self)
        self.config_tab = ConfigTab(self)
        self.vision_tab = VisionTab(self)
        self.log_tab = LogTab(self)
        
        # Connect signals
        self.config_tab.connection_toggled.connect(self.toggle_connection)
        self.config_tab.calibration_requested.connect(self.send_calibration)
        self.config_tab.log_message.connect(self.add_log)
        
        self.main_control.goto_command.connect(self.send_goto)
        self.main_control.program_command.connect(self.execute_program_command)
        self.main_control.log_message.connect(self.add_log)
        
        self.vision_tab.log_message.connect(self.add_log)
        
        # Add tabs
        self.tab_widget.addTab(self.main_control, "🎮 MAIN CONTROL")
        self.tab_widget.addTab(self.config_tab, "⚙️ CONFIG")
        self.tab_widget.addTab(self.vision_tab, "📷 VISION")
        self.tab_widget.addTab(self.log_tab, "📋 SYSTEM LOG")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_status_bar(self):
        """Setup status bar"""
        status_bar = self.statusBar()
        
        self.main_status_label = QLabel("● Disconnected")
        self.main_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        status_bar.addPermanentWidget(self.main_status_label)
        status_bar.addPermanentWidget(QLabel("|"))
        
        self.position_status = QLabel("📍 X:0.00 mm | Y:0.00 mm | Z:-550.00 mm")
        status_bar.addPermanentWidget(self.position_status)
        
        # Timer for updating time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.time_label = QLabel()
        status_bar.addPermanentWidget(self.time_label)
        self.update_time()
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.current_theme == "light":
            self.apply_theme("dark")
            self.add_log("INFO", "Switched to dark theme")
        else:
            self.apply_theme("light")
            self.add_log("INFO", "Switched to light theme")
    
    def update_time(self):
        """Update time in status bar"""
        self.time_label.setText(f"🕐 {get_timestamp()}")
    
    def add_log(self, level, message):
        """Add log message"""
        if hasattr(self, 'log_tab') and self.log_tab:
            self.log_tab.add_log(level, message)
    
    # ===== SERIAL COMMUNICATION =====
    
    def toggle_connection(self, connect, port, baudrate):
        """Toggle connection"""
        if connect:
            self.add_log("INFO", f"Connecting to {port} at {baudrate} baud...")
            self.serial_thread.connect(port, baudrate)
        else:
            self.add_log("INFO", "Disconnecting...")
            self.serial_thread.disconnect()
    
    def on_connection_status(self, connected, message):
        """Handle connection status"""
        # Update config tab
        self.config_tab.update_connection_status(connected, message)
        
        # Update main control
        self.main_control.set_connection_status(connected)
        
        # Update status bar
        if connected:
            self.main_status_label.setText("● Connected")
            self.main_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.connected = True
            self.add_log("INFO", f"✅ {message}")
            
            # Send test command
            QTimer.singleShot(100, lambda: self.serial_thread.send_command("TEST"))
        else:
            self.main_status_label.setText("● Disconnected")
            self.main_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
            self.connected = False
            self.add_log("WARNING" if "failed" in message.lower() else "INFO", message)
    
    def on_serial_data(self, data):
        """Handle incoming serial data"""
        self.config_tab.add_to_terminal(f"← {data}")
        self.config_tab.update_calibration_status(data)
        self.add_log("DEBUG", f"RX: {data}")
        
        if data.startswith("POS:"):
            try:
                parts = data[4:].split(',')
                if len(parts) >= 3:
                    x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                    self.main_control.update_position_display(x, y, z)
                    self.position_status.setText(f"📍 X:{x:.2f} mm | Y:{y:.2f} mm | Z:{z:.2f} mm")
            except:
                pass
        
        elif "ready at 0" in data.lower() or "calibration successful" in data.lower():
            self.add_log("INFO", "✅ Calibration completed successfully")
    
    def on_serial_error(self, error):
        """Handle serial errors"""
        self.config_tab.add_to_terminal(f"✗ ERROR: {error}")
        self.add_log("ERROR", error)
    
    def send_calibration(self):
        """Send calibration command"""
        if not self.connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to a device first!")
            return
        
        self.config_tab.add_to_terminal("→ JC")
        self.serial_thread.send_command("JC")
        self.add_log("INFO", "Calibration command sent (JC)")
    
    def send_goto(self, x, y, z, time_val):
        """Send GOTO command"""
        if not self.connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to a device first!")
            return
        
        command = format_goto_command(x, y, z, time_val)
        self.serial_thread.send_command(command)
        self.config_tab.add_to_terminal(f"→ {command}")
        self.add_log("INFO", f"GOTO: X={x}, Y={y}, Z={z}, T={time_val}s")
    
    # ===== UPDATED: execute_program_command with G-code buffer support =====
    def execute_program_command(self, command):
        """Execute program command - with GCODE_BUFFER support"""
        if not self.connected:
            return
        
        self.config_tab.add_to_terminal(f"→ Exec: {command}")
        
        # Handle GCODE_BUFFER command (multiple points at once)
        if command.startswith("GCODE_BUFFER"):
            # Send directly to Arduino - planner will handle it
            self.serial_thread.send_command(command)
            
            # Count points for log
            point_count = count_points_in_buffer(command)
            self.add_log("INFO", f"Sent {point_count} points to motion planner")
        
        # Handle regular G00/G01 commands
        elif "G01" in command or "G00" in command:
            from utils import extract_value
            x = extract_value(command, 'X')
            y = extract_value(command, 'Y')
            z = extract_value(command, 'Z')
            
            if x and y and z:
                try:
                    # Use time from main control
                    time_val = self.main_control.goto_time_spin.value()
                    goto_cmd = format_goto_command(float(x), float(y), float(z), time_val)
                    self.serial_thread.send_command(goto_cmd)
                except Exception as e:
                    self.add_log("ERROR", f"Failed to send GOTO: {e}")  
        
        # Handle other commands (WAIT, etc.)
        else:
            self.serial_thread.send_command(command)
    
    def emergency_stop(self):
        """Emergency stop"""
        if self.connected:
            self.serial_thread.send_command("EMERGENCY_STOP")
        self.add_log("WARNING", "⚠️ EMERGENCY STOP ACTIVATED")
        QMessageBox.warning(self, "Emergency Stop", "Emergency stop activated!")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
            "Delta Robot Controller v1.0\n"
            "WeVOIS Pro Edition\n\n"
            "Features:\n"
            "• Light/Dark theme toggle (Ctrl+T)\n"
            "• Professional UI with consistent styling\n"
            "• Real-time serial communication\n"
            "• Program management with playback controls\n"
            "• G-code buffer mode for continuous motion\n\n"
            "© 2024 All rights reserved")
    
    def closeEvent(self, event):
        """Clean up on close"""
        self.add_log("INFO", "Shutting down...")
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.disconnect()
            self.serial_thread.wait(2000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set default light theme
    app.setPalette(ThemeManager.get_light_palette())
    
    # Set application-wide font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = DeltaRobotGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()