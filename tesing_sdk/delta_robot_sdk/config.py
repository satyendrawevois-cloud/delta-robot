from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import serial
import serial.tools.list_ports
import json
import sys
import time
import os
from datetime import datetime

# ========== CONFIG FUNCTIONS ==========
CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from file"""
    default_config = {
        "port": "",
        "baudrate": 115200,
        "timeout": 1,
        "auto_connect": False
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return default_config

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# ========== SERIAL FUNCTIONS ==========
def get_available_ports():
    """Get list of available serial ports"""
    ports = []
    try:
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'display': f"{port.device} - {port.description}"
            })
    except Exception as e:
        print(f"Error getting ports: {e}")
    
    return ports

# ========== MAIN CONFIG TAB CLASS ==========
class ConfigTab(QWidget):
    """Configuration tab with compact 3-column layout"""
    
    # Signals
    connection_toggled = pyqtSignal(bool, str, int)
    calibration_requested = pyqtSignal()
    log_message = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.connected = False
        self.current_port = ""
        self.current_baudrate = 115200
        
        # ========== COLOR CONFIGURATION ==========
        # Aap yahan sab colors manually change kar sakte hain
        
        # Main Window Colors
        self.window_bg = "#1e1e1e"
        self.window_text = "#ffffff"
        
        # Column Background Colors
        self.comm_column_bg = "#1a1a1a"
        self.status_column_bg = "#1a1a1a"
        self.terminal_column_bg = "#1a1a1a"
        
        # Column Border Colors
        self.comm_column_border = "#4caf50"      # Green
        self.status_column_border = "#ff9800"     # Orange
        self.terminal_column_border = "#2196f3"   # Blue
        
        # Section Background Colors
        self.section_bg = "#252525"
        self.section_border = "#3a3a3a"
        
        # Header Colors
        self.header_bg = "#252525"
        self.header_text_comm = "#4caf50"
        self.header_text_status = "#ff9800"
        self.header_text_terminal = "#2196f3"
        
        # Label Colors
        self.label_text_primary = "#ffffff"
        self.label_text_secondary = "#888888"
        self.label_text_success = "#4caf50"
        self.label_text_warning = "#ff9800"
        self.label_text_error = "#f44336"
        self.label_text_info = "#2196f3"
        
        # Input Field Colors
        self.input_bg = "#2d2d2d"
        self.input_text = "#ffffff"
        self.input_border = "#4caf50"
        self.input_border_hover = "#6ab04c"
        
        # Button Colors
        self.btn_connect_bg = "#4caf50"
        self.btn_connect_text = "#ffffff"
        self.btn_connect_hover = "#45a049"
        
        self.btn_disconnect_bg = "#f44336"
        self.btn_disconnect_text = "#ffffff"
        self.btn_disconnect_hover = "#d32f2f"
        
        self.btn_calibrate_bg = "#ff9800"
        self.btn_calibrate_text = "#ffffff"
        self.btn_calibrate_hover = "#f57c00"
        
        self.btn_refresh_bg = "#2d2d2d"
        self.btn_refresh_text = "#4caf50"
        self.btn_refresh_hover = "#3a3a3a"
        
        self.btn_terminal_bg = "#2d2d2d"
        self.btn_terminal_text = "#2196f3"
        self.btn_terminal_hover = "#3a3a3a"
        
        # Status Indicator Colors
        self.indicator_connected = "#4caf50"
        self.indicator_disconnected = "#888888"
        self.indicator_error = "#f44336"
        self.indicator_warning = "#ff9800"
        
        # Terminal Colors
        self.terminal_bg = "#0a0a1a"
        self.terminal_text = "#00ff00"
        self.terminal_border = "#2196f3"
        
        # Status Message Colors
        self.msg_success_bg = "#1e2a3a"
        self.msg_success_text = "#4caf50"
        self.msg_error_bg = "#2a1e1e"
        self.msg_error_text = "#f44336"
        self.msg_warning_bg = "#2a2a1e"
        self.msg_warning_text = "#ff9800"
        
        self.init_ui()
        self.load_saved_config()
        self.log_message.connect(self._handle_log)
        QTimer.singleShot(100, self.refresh_ports)
        
    def init_ui(self):
        """Initialize the compact 3-column UI"""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Set window background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.window_bg};
                color: {self.window_text};
            }}
        """)
        
        # Create three columns
        self.create_communication_column(main_layout)
        self.create_status_column(main_layout)
        self.create_terminal_column(main_layout)
        
    def create_communication_column(self, parent_layout):
        """Column 1: Communication settings"""
        col = QFrame()
        col.setStyleSheet(f"""
            QFrame {{
                background-color: {self.comm_column_bg};
                border: 2px solid {self.comm_column_border};
                border-radius: 6px;
            }}
        """)
        col.setFixedWidth(280)
        
        layout = QVBoxLayout(col)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = self.create_header("🔌 COMMUNICATION", self.header_text_comm)
        layout.addWidget(header)
        
        # Port selection section
        port_frame = QFrame()
        port_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.section_bg};
                border: 1px solid {self.section_border};
                border-radius: 6px;
            }}
        """)
        port_layout = QVBoxLayout(port_frame)
        port_layout.setSpacing(5)
        port_layout.setContentsMargins(10, 10, 10, 10)
        
        port_label = QLabel("PORT")
        port_label.setStyleSheet(f"""
            color: {self.label_text_primary};
            font-size: 14px;
            font-weight: bold;
        """)
        port_layout.addWidget(port_label)
        
        # Port selection with refresh
        port_select = QHBoxLayout()
        port_select.setSpacing(10)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(28)
        self.port_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.input_bg};
                color: {self.input_text};
                border: 1px solid {self.input_border};
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 14px;
            }}
            QComboBox:hover {{
                border: 2px solid {self.input_border_hover};
            }}
            QComboBox::drop-down {{
                width: 30px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {self.input_border};
            }}
        """)
        port_select.addWidget(self.port_combo)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(28, 28)
        self.refresh_btn.setToolTip("Refresh ports")
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.btn_refresh_bg};
                color: {self.btn_refresh_text};
                border: 1px solid {self.btn_refresh_text};
                border-radius: 3px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.btn_refresh_hover};
            }}
        """)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_select.addWidget(self.refresh_btn)
        
        port_layout.addLayout(port_select)
        
        # Port info
        self.port_info = QLabel("No port selected")
        self.port_info.setStyleSheet(f"""
            color: {self.label_text_secondary};
            font-size: 10px;
            padding: 2px 0;
        """)
        port_layout.addWidget(self.port_info)
        
        layout.addWidget(port_frame)
        
        # Baud rate section
        baud_frame = QFrame()
        baud_frame.setStyleSheet(port_frame.styleSheet())
        baud_layout = QVBoxLayout(baud_frame)
        baud_layout.setSpacing(3)
        baud_layout.setContentsMargins(8, 8, 8, 8)
        
        baud_label = QLabel("BAUD RATE")
        baud_label.setStyleSheet(f"""
            color: {self.label_text_primary};
            font-size: 14px;
            font-weight: bold;
        """)
        baud_layout.addWidget(baud_label)
        
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "250000"])
        self.baud_combo.setCurrentText("115200")
        self.baud_combo.setEditable(True)
        self.baud_combo.setMinimumHeight(28)
        self.baud_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.input_bg};
                color: {self.input_text};
                border: 1px solid {self.input_border};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QComboBox:hover {{
                border: 1px solid {self.input_border_hover};
            }}
        """)
        baud_layout.addWidget(self.baud_combo)
        
        self.baud_info = QLabel("8N1 (Default)")
        self.baud_info.setStyleSheet(f"""
            color: {self.label_text_secondary};
            font-size: 10px;
            padding: 2px 0;
        """)
        baud_layout.addWidget(self.baud_info)
        
        layout.addWidget(baud_frame)
        
        # Connection buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet(port_frame.styleSheet())
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(5)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        
        self.connect_btn = QPushButton("🔌 CONNECT")
        self.connect_btn.setMinimumHeight(32)
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.btn_connect_bg};
                color: {self.btn_connect_text};
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.btn_connect_hover};
            }}
            QPushButton:disabled {{
                background-color: #555;
            }}
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("⛔ DISCONNECT")
        self.disconnect_btn.setMinimumHeight(32)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.btn_disconnect_bg};
                color: {self.btn_disconnect_text};
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.btn_disconnect_hover};
            }}
            QPushButton:disabled {{
                background-color: #555;
            }}
        """)
        self.disconnect_btn.clicked.connect(self.disconnect)
        btn_layout.addWidget(self.disconnect_btn)
        
        layout.addWidget(btn_frame)
        layout.addStretch()
        parent_layout.addWidget(col)
    
    def create_status_column(self, parent_layout):
        """Column 2: Status and calibration"""
        col = QFrame()
        col.setStyleSheet(f"""
            QFrame {{
                background-color: {self.status_column_bg};
                border: 2px solid {self.status_column_border};
                border-radius: 6px;
            }}
        """)
        col.setFixedWidth(250)
        
        layout = QVBoxLayout(col)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = self.create_header("📊 STATUS", self.header_text_status)
        layout.addWidget(header)
        
        # Status indicators
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.section_bg};
                border: 1px solid {self.section_border};
                border-radius: 4px;
            }}
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(5)
        status_layout.setContentsMargins(8, 8, 8, 8)
        
        status_title = QLabel("STATUS INDICATORS")
        status_title.setStyleSheet(f"""
            color: {self.label_text_primary};
            font-size: 14px;
            font-weight: bold;
        """)
        status_layout.addWidget(status_title)
        
        # System status
        sys_status = QHBoxLayout()
        self.sys_indicator = QLabel("●")
        self.sys_indicator.setStyleSheet(f"color: {self.indicator_connected}; font-size: 14px;")
        sys_status.addWidget(self.sys_indicator)
        
        self.system_label = QLabel("System:")
        self.system_label.setStyleSheet(f"""
            QLabel {{
                color: {self.label_text_success};
                background-color: {self.section_bg};
                font-weight: bold;
                padding: 2px 5px;
                border-radius: 3px;
            }}
        """)
        sys_status.addWidget(self.system_label)

        self.sys_status_text = QLabel("Ready")
        self.sys_status_text.setStyleSheet(f"color: {self.label_text_primary}; font-weight: bold;")
        sys_status.addWidget(self.sys_status_text)
        sys_status.addStretch()
        status_layout.addLayout(sys_status)
        
        # Port status
        port_status = QHBoxLayout()
        self.port_indicator = QLabel("○")
        self.port_indicator.setStyleSheet(f"color: {self.indicator_disconnected}; font-size: 14px;")
        port_status.addWidget(self.port_indicator)
        
        port_label = QLabel("Port:")
        port_label.setStyleSheet(f"color: {self.label_text_primary};")
        port_status.addWidget(port_label)
        
        self.port_status_text = QLabel("None")
        self.port_status_text.setStyleSheet(f"color: {self.label_text_primary};")
        port_status.addWidget(self.port_status_text)
        port_status.addStretch()
        status_layout.addLayout(port_status)
        
        # Baud status
        baud_status = QHBoxLayout()
        self.baud_indicator = QLabel("○")
        self.baud_indicator.setStyleSheet(f"color: {self.indicator_disconnected}; font-size: 14px;")
        baud_status.addWidget(self.baud_indicator)
        
        baud_label = QLabel("Baud:")
        baud_label.setStyleSheet(f"color: {self.label_text_primary};")
        baud_status.addWidget(baud_label)
        
        self.baud_status_text = QLabel("115200")
        self.baud_status_text.setStyleSheet(f"color: {self.label_text_primary};")
        baud_status.addWidget(self.baud_status_text)
        baud_status.addStretch()
        status_layout.addLayout(baud_status)
        
        layout.addWidget(status_frame)
        
        # Calibration control
        calib_frame = QFrame()
        calib_frame.setStyleSheet(status_frame.styleSheet())
        calib_layout = QVBoxLayout(calib_frame)
        calib_layout.setSpacing(5)
        calib_layout.setContentsMargins(8, 8, 8, 8)
        
        calib_title = QLabel("CALIBRATION CONTROL")
        calib_title.setStyleSheet(f"color: {self.label_text_secondary}; font-size: 10px; font-weight: bold;")
        calib_layout.addWidget(calib_title)
        
        self.calibrate_btn = QPushButton("🎯 START CALIBRATION")
        self.calibrate_btn.setMinimumHeight(36)
        self.calibrate_btn.setEnabled(False)
        self.calibrate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.btn_calibrate_bg};
                color: {self.btn_calibrate_text};
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.btn_calibrate_hover};
            }}
            QPushButton:disabled {{
                background-color: #555;
            }}
        """)
        self.calibrate_btn.clicked.connect(self.request_calibration)
        calib_layout.addWidget(self.calibrate_btn)
        
        # Calibration status
        calib_status = QHBoxLayout()
        calib_label = QLabel("Status:")
        calib_label.setStyleSheet(f"color: {self.label_text_primary};")
        calib_status.addWidget(calib_label)
        
        self.calib_status_text = QLabel("⚪ Ready")
        self.calib_status_text.setStyleSheet(f"color: {self.label_text_primary};")
        calib_status.addWidget(self.calib_status_text)
        calib_status.addStretch()
        calib_layout.addLayout(calib_status)
        
        layout.addWidget(calib_frame)
        layout.addStretch()
        parent_layout.addWidget(col)
    
    def create_terminal_column(self, parent_layout):
        """Column 3: Terminal monitor"""
        col = QFrame()
        col.setStyleSheet(f"""
            QFrame {{
                background-color: {self.terminal_column_bg};
                border: 2px solid {self.terminal_column_border};
                border-radius: 6px;
            }}
        """)
        
        layout = QVBoxLayout(col)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = self.create_header("📟 TERMINAL", self.header_text_terminal)
        layout.addWidget(header)
        
        # Terminal display
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMinimumHeight(200)
        self.terminal.setFont(QFont("Consolas", 9))
        self.terminal.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.terminal_bg};
                color: {self.terminal_text};
                border: 1px solid {self.terminal_border};
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas';
            }}
        """)
        layout.addWidget(self.terminal)
        
        # Terminal controls
        control_frame = QFrame()
        control_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.section_bg};
                border: 1px solid {self.section_border};
                border-radius: 4px;
            }}
        """)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(5)
        control_layout.setContentsMargins(8, 8, 8, 8)
        
        self.clear_btn = QPushButton("🗑️ CLEAR")
        self.clear_btn.setMinimumHeight(28)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.btn_terminal_bg};
                color: {self.btn_terminal_text};
                border: 1px solid {self.btn_terminal_text};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.btn_terminal_hover};
            }}
        """)
        self.clear_btn.clicked.connect(self.clear_terminal)
        control_layout.addWidget(self.clear_btn)
        
        self.copy_btn = QPushButton("📋 COPY")
        self.copy_btn.setMinimumHeight(28)
        self.copy_btn.setStyleSheet(self.clear_btn.styleSheet())
        self.copy_btn.clicked.connect(self.copy_terminal)
        control_layout.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("💾 SAVE")
        self.save_btn.setMinimumHeight(28)
        self.save_btn.setStyleSheet(self.clear_btn.styleSheet())
        self.save_btn.clicked.connect(self.save_terminal)
        control_layout.addWidget(self.save_btn)
        
        control_layout.addStretch()
        layout.addWidget(control_frame)
        
        # Status message
        msg_frame = QFrame()
        msg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.msg_success_bg};
                border: 1px solid {self.terminal_column_border};
                border-radius: 6px;
            }}
        """)
        msg_layout = QHBoxLayout(msg_frame)
        msg_layout.setContentsMargins(10, 8, 10, 8)
        
        self.status_message = QLabel("[15:42:16] ✓ Found 4 ports")
        self.status_message.setStyleSheet(f"color: {self.msg_success_text}; font-size: 14px;")
        msg_layout.addWidget(self.status_message)
        
        layout.addWidget(msg_frame)
        parent_layout.addWidget(col)
    
    def create_header(self, text, color):
        """Create a column header"""
        header = QLabel(text)
        header.setStyleSheet(f"""
            color: {color};
            font-weight: bold;
            font-size: 13px;
            padding: 4px;
            background-color: {self.header_bg};
            border: 1px solid {color};
            border-radius: 4px;
        """)
        header.setAlignment(Qt.AlignCenter)
        return header
    
    def refresh_ports(self):
        """Refresh available serial ports"""
        self.port_combo.clear()
        ports = get_available_ports()
        
        if ports:
            for port in ports:
                self.port_combo.addItem(port['display'], port['device'])
            self.port_info.setText(f"{len(ports)} port(s) available")
            self.add_to_terminal(f"[{self.get_time()}] ✓ Found {len(ports)} ports")
        else:
            self.port_combo.addItem("No ports available")
            self.port_info.setText("No ports detected")
            self.add_to_terminal(f"[{self.get_time()}] ✗ No ports found")
    
    def toggle_connection(self):
        """Connect to selected port"""
        if not self.port_combo.currentData():
            QMessageBox.warning(self, "Error", "Please select a port")
            return
        
        port = self.port_combo.currentData()
        baudrate = int(self.baud_combo.currentText())
        
        self.connect_btn.setEnabled(False)
        self.add_to_terminal(f"[{self.get_time()}] ⟳ Connecting to {port} at {baudrate}...")
        
        # Simulate connection (replace with actual serial connection)
        QTimer.singleShot(1000, lambda: self.connection_successful(port, baudrate))
    
    def connection_successful(self, port, baudrate):
        """Handle successful connection"""
        self.connected = True
        self.current_port = port
        self.current_baudrate = baudrate
        
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.calibrate_btn.setEnabled(True)
        
        # Update status indicators
        self.sys_indicator.setStyleSheet(f"color: {self.indicator_connected}; font-size: 14px;")
        self.sys_status_text.setText("Connected")
        self.sys_status_text.setStyleSheet(f"color: {self.indicator_connected}; font-weight: bold;")
        
        self.port_indicator.setStyleSheet(f"color: {self.indicator_connected}; font-size: 14px;")
        self.port_status_text.setText(port)
        self.port_status_text.setStyleSheet(f"color: {self.indicator_connected};")
        
        self.baud_indicator.setStyleSheet(f"color: {self.indicator_connected}; font-size: 14px;")
        self.baud_status_text.setText(str(baudrate))
        self.baud_status_text.setStyleSheet(f"color: {self.indicator_connected};")
        
        self.status_message.setText(f"[{self.get_time()}] ✓ Connected to {port}")
        self.status_message.setStyleSheet(f"color: {self.msg_success_text}; font-size: 14px; font-weight: bold;")
        
        self.add_to_terminal(f"[{self.get_time()}] ✓ Connection successful")
        self.add_to_terminal(f"[{self.get_time()}] ● Ready for commands")
        
        self.connection_toggled.emit(True, port, baudrate)
    
    def disconnect(self):
        """Disconnect from port"""
        self.connected = False
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.calibrate_btn.setEnabled(False)
        
        # Update status indicators
        self.sys_indicator.setStyleSheet(f"color: {self.indicator_error}; font-size: 14px;")
        self.sys_status_text.setText("Disconnected")
        self.sys_status_text.setStyleSheet(f"color: {self.indicator_error};")
        
        self.port_indicator.setStyleSheet(f"color: {self.indicator_disconnected}; font-size: 14px;")
        self.port_status_text.setText("None")
        self.port_status_text.setStyleSheet(f"color: {self.indicator_disconnected};")
        
        self.baud_indicator.setStyleSheet(f"color: {self.indicator_disconnected}; font-size: 14px;")
        
        self.status_message.setText(f"[{self.get_time()}] ✗ Disconnected")
        self.status_message.setStyleSheet(f"color: {self.indicator_error}; font-size: 10px;")
        
        self.add_to_terminal(f"[{self.get_time()}] ✗ Disconnected")
        self.connection_toggled.emit(False, "", 0)
    
    def request_calibration(self):
        """Request calibration"""
        if not self.connected:
            QMessageBox.warning(self, "Error", "Please connect first")
            return
        
        reply = QMessageBox.question(
            self, "Calibration", 
            "Start calibration process?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.calib_status_text.setText("⚙️ Calibrating...")
            self.calib_status_text.setStyleSheet(f"color: {self.indicator_warning};")
            self.add_to_terminal(f"[{self.get_time()}] → JC")
            self.add_to_terminal(f"[{self.get_time()}] ⚙️ Calibration started")
            self.calibration_requested.emit()
            
            # YAHAN SE DUMMY TIMER HATAYA
            # QTimer.singleShot(3000, self.calibration_complete)
    
    def calibration_complete(self):
        """Handle calibration completion"""
        self.calib_status_text.setText("✅ Calibrated")
        self.calib_status_text.setStyleSheet(f"color: {self.indicator_connected};")
        self.add_to_terminal(f"[{self.get_time()}] ✓ Calibration complete")
        self.add_to_terminal(f"[{self.get_time()}] ● Ready at zero position")
    
    def update_calibration_status(self, data):
        """Update calibration status from serial data"""
        # Terminal mein data dikhao
        self.add_to_terminal(f"[{self.get_time()}] {data}")
        
        # Calibration complete ke keywords check karo
        calibration_complete_keywords = [
            "calibration complete", 
            "calibration successful", 
            "calibrated", 
            "calibration done",
            "calib ok",
            "ready at zero",
            "zero position",
            "calibration finished",
            "success"
        ]
        
        # Calibration start ke keywords check karo
        calibration_start_keywords = [
            "calibrating",
            "calibration started",
            "calib start",
            "calibration begin",
            "started calibration"
        ]
        
        # Check for calibration complete
        if any(keyword in data.lower() for keyword in calibration_complete_keywords):
            self.calib_status_text.setText("✅ Calibrated")
            self.calib_status_text.setStyleSheet(f"color: {self.indicator_connected};")
            self.add_to_terminal(f"[{self.get_time()}] ✓ Calibration complete")
            self.add_to_terminal(f"[{self.get_time()}] ● Ready at zero position")
        
        # Check for calibration in progress
        elif any(keyword in data.lower() for keyword in calibration_start_keywords):
            self.calib_status_text.setText("⚙️ Calibrating...")
            self.calib_status_text.setStyleSheet(f"color: {self.indicator_warning};")
        
        # Agar koi progress message hai to usko bhi show karo
        elif "progress" in data.lower() or "%" in data:
            # Progress message ko calibration status mein dikhao
            self.calib_status_text.setText(f"⚙️ {data[:30]}...")
            self.calib_status_text.setStyleSheet(f"color: {self.indicator_warning};")
    
    # ========== TERMINAL METHODS ==========
    def add_to_terminal(self, text):
        """Add text to terminal"""
        self.terminal.append(text)
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.terminal.setTextCursor(cursor)
    
    def clear_terminal(self):
        """Clear terminal"""
        self.terminal.clear()
        self.add_to_terminal(f"[{self.get_time()}] Terminal cleared")
    
    def copy_terminal(self):
        """Copy terminal content to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.terminal.toPlainText())
        self.add_to_terminal(f"[{self.get_time()}] ✓ Copied to clipboard")
    
    def save_terminal(self):
        """Save terminal content to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Terminal Log", "terminal_log.txt", "Text Files (*.txt)"
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.terminal.toPlainText())
                self.add_to_terminal(f"[{self.get_time()}] ✓ Saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
    
    def get_time(self):
        """Get current timestamp"""
        return datetime.now().strftime("%H:%M:%S")
    
    def get_selected_port(self):
        """Get selected port device"""
        return self.port_combo.currentData() if self.port_combo.currentData() else None
    
    def load_saved_config(self):
        """Load saved configuration"""
        config = load_config()
        if config:
            saved_baud = config.get("baudrate", 115200)
            index = self.baud_combo.findText(str(saved_baud))
            if index >= 0:
                self.baud_combo.setCurrentIndex(index)
    
    def update_connection_status(self, connected, message):
        """Update connection status from external signal"""
        if connected:
            self.connection_successful(self.current_port, self.current_baudrate)
        else:
            self.disconnect()
        self.add_to_terminal(f"[{self.get_time()}] {message}")
    
    def _handle_log(self, level, message):
        """Handle log messages"""
        if level in ["ERROR", "WARNING"]:
            self.add_to_terminal(f"[{self.get_time()}] {level}: {message}")
            self.status_message.setText(f"[{self.get_time()}] {level}: {message}")
            if level == "ERROR":
                self.status_message.setStyleSheet(f"color: {self.indicator_error}; font-size: 10px;")
                self.status_message.setStyleSheet(f"background-color: {self.msg_error_bg};")
            else:
                self.status_message.setStyleSheet(f"color: {self.indicator_warning}; font-size: 10px;")
                self.status_message.setStyleSheet(f"background-color: {self.msg_warning_bg};")

class MainWindow(QMainWindow):
    """Main window to test the ConfigTab"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Device Configuration - Compact Layout")
        self.setGeometry(100, 100, 950, 450)
        self.setMinimumSize(900, 400)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add ConfigTab
        self.config_tab = ConfigTab(self)
        layout.addWidget(self.config_tab)
        
        # Connect signals
        self.config_tab.connection_toggled.connect(self.on_connection_toggled)
        self.config_tab.calibration_requested.connect(self.on_calibration_requested)
        self.config_tab.log_message.connect(self.on_log_message)
    
    def on_connection_toggled(self, connected, port, baudrate):
        """Handle connection toggled"""
        if connected:
            print(f"Connected to {port} at {baudrate}")
        else:
            print("Disconnected")
    
    def on_calibration_requested(self):
        """Handle calibration requested"""
        print("Calibration requested")
        self.config_tab.add_to_terminal(f"[{self.config_tab.get_time()}] Processing calibration...")
    
    def on_log_message(self, level, message):
        """Handle log messages"""
        print(f"[{level}] {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    # Add some initial terminal messages
    window.config_tab.add_to_terminal(f"[{window.config_tab.get_time()}] ⚡ System initialized")
    window.config_tab.add_to_terminal(f"[{window.config_tab.get_time()}] ● Ready for connection")
    
    sys.exit(app.exec_())