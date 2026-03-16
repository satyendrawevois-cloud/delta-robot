from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import re
from utils import extract_value, format_goto_command

class MainControlTab(QWidget):
    """Main Control tab with Motion, Program, and Position control"""
    
    # Signals
    goto_command = pyqtSignal(float, float, float, float)  # x, y, z, time
    program_command = pyqtSignal(str)  # command to execute
    log_message = pyqtSignal(str, str)  # level, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_position = [0, 0, -550]
        self.program_running = False
        self.program_paused = False
        self.current_line = 0
        self.program_lines = []
        self.connected = False
        
        self.init_ui()
        self.update_program_lines()
        
        # Connect internal signals
        self.log_message.connect(self._handle_log)
        
    def init_ui(self):
        """Initialize UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel - Motion Control (Narrow - 20% width)
        left_panel = self.create_left_panel()
        left_panel.setMaximumWidth(250)  # Fixed narrow width
        layout.addWidget(left_panel, 2)  # Reduced stretch factor
        
        # Center panel - Program Management (Wide - 50% width)
        center_panel = self.create_center_panel()
        layout.addWidget(center_panel, 5)
        
        # Right panel - Position Control (35% width)
        right_panel = self.create_right_panel()
        layout.addWidget(right_panel, 3)
    
    def create_left_panel(self):
        """Create narrow left panel with Motion Control"""
        panel = QGroupBox("🎮 Motion Control")
        panel.setStyleSheet("""
            QGroupBox { 
                font-size: 14px; 
                font-weight: bold;
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 15, 10, 10)

        ##########################################################
        #########################################################

        # # Motion parameters
        # motion_group = QGroupBox("⚙️ Parameters")
        # motion_group.setStyleSheet("QGroupBox { font-size: 13px; }")
        # motion_layout = QFormLayout(motion_group)
        # motion_layout.setVerticalSpacing(10)
        # motion_layout.setLabelAlignment(Qt.AlignRight)
        
        # # Default Time
        # self.time_spin = QDoubleSpinBox()
        # self.time_spin.setRange(0.1, 10.0)
        # self.time_spin.setValue(0.9)  # Changed to 0.90 as per image
        # self.time_spin.setSingleStep(0.1)
        # self.time_spin.setSuffix(" s")
        # self.time_spin.setMinimumWidth(100)
        # motion_layout.addRow("Time (s):", self.time_spin)
        
        # # Acceleration
        # self.accel_spin = QSpinBox()
        # self.accel_spin.setRange(1, 100)
        # self.accel_spin.setValue(15)
        # self.accel_spin.setSuffix("%")
        # self.accel_spin.setMinimumWidth(100)
        # motion_layout.addRow("Accel (%):", self.accel_spin)
        
        # # Smoothing
        # self.smooth_spin = QSpinBox()
        # self.smooth_spin.setRange(0, 100)
        # self.smooth_spin.setValue(30)  # Changed to 30 as per image
        # self.smooth_spin.setMinimumWidth(100)
        # motion_layout.addRow("Smoothing:", self.smooth_spin)
        
        # layout.addWidget(motion_group)
        
        # # Command Teaching (replaced with Manual Program Entry as per image 1)
        # teach_group = QGroupBox("📝 Manual Program Entry")
        # teach_group.setStyleSheet("QGroupBox { font-size: 13px; }")
        # teach_layout = QVBoxLayout(teach_group)
        # teach_layout.setSpacing(8)
        
        # # Buttons as per first image: Copy, Paste, Replace, Open .txt File, Reload
        # btn_layout1 = QHBoxLayout()
        # copy_btn = QPushButton("Copy")
        # copy_btn.setMinimumHeight(30)
        # copy_btn.clicked.connect(self.copy_selected_line)
        # btn_layout1.addWidget(copy_btn)
        
        # paste_btn = QPushButton("Paste")
        # paste_btn.setMinimumHeight(30)
        # paste_btn.clicked.connect(self.paste_line)
        # btn_layout1.addWidget(paste_btn)
        
        # replace_btn = QPushButton("Replace")
        # replace_btn.setMinimumHeight(30)
        # replace_btn.clicked.connect(self.replace_line)
        # btn_layout1.addWidget(replace_btn)
        
        # teach_layout.addLayout(btn_layout1)
        
        # btn_layout2 = QHBoxLayout()
        # open_btn = QPushButton("Open .txt File")
        # open_btn.setMinimumHeight(30)
        # open_btn.clicked.connect(self.load_program)
        # btn_layout2.addWidget(open_btn)
        
        # reload_btn = QPushButton("Reload")
        # reload_btn.setMinimumHeight(30)
        # reload_btn.clicked.connect(self.reload_program)
        # btn_layout2.addWidget(reload_btn)
        
        # teach_layout.addLayout(btn_layout2)
        
        # layout.addWidget(teach_group)

        ########################################################
        #################################################33333
        
        # Position Commands (as per image 2)
        pos_group = QGroupBox("📍 Position Commands")
        pos_group.setStyleSheet("QGroupBox { font-size: 13px; }")
        pos_layout = QVBoxLayout(pos_group)
        pos_layout.setSpacing(5)
        
        move_j_btn = QPushButton("Move J")
        move_j_btn.setMinimumHeight(30)
        move_j_btn.clicked.connect(self.move_j)
        pos_layout.addWidget(move_j_btn)
        
        teach_pos_btn = QPushButton("Teach New Position")
        teach_pos_btn.setMinimumHeight(30)
        teach_pos_btn.clicked.connect(self.teach_position)
        pos_layout.addWidget(teach_pos_btn)
        
        modify_pos_btn = QPushButton("Modify Position")
        modify_pos_btn.setMinimumHeight(30)
        modify_pos_btn.clicked.connect(self.modify_selected_position)
        pos_layout.addWidget(modify_pos_btn)
        
        delete_pos_btn = QPushButton("Delete")
        delete_pos_btn.setMinimumHeight(30)
        delete_pos_btn.clicked.connect(self.delete_selected)
        pos_layout.addWidget(delete_pos_btn)
        
        return_btn = QPushButton("Return")
        return_btn.setMinimumHeight(30)
        return_btn.clicked.connect(self.return_to_home)
        pos_layout.addWidget(return_btn)
        
        layout.addWidget(pos_group)
        
        # Connection status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.conn_status_label = QLabel("● Disconnected")
        self.conn_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        status_layout.addWidget(self.conn_status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        layout.addStretch()
        return panel
    
    def create_center_panel(self):
        """Create wide center panel with Program Management"""
        panel = QGroupBox("📋 Program Management")
        panel.setStyleSheet("""
            QGroupBox { 
                font-size: 14px; 
                font-weight: bold;
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 15, 12, 12)
        
        # Program file controls
        file_layout = QHBoxLayout()
        
        self.program_label = QLabel("📄 No file loaded...")
        self.program_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        file_layout.addWidget(self.program_label)
        
        # File buttons
        load_btn = QPushButton("📂 Load")
        load_btn.setMaximumWidth(100)
        load_btn.clicked.connect(self.load_program)
        file_layout.addWidget(load_btn)
        
        new_btn = QPushButton("🆕 New")
        new_btn.setMaximumWidth(100)
        new_btn.clicked.connect(self.new_program)
        file_layout.addWidget(new_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.setMaximumWidth(100)
        save_btn.clicked.connect(self.save_program)
        file_layout.addWidget(save_btn)
        file_layout.addStretch()
        
        layout.addLayout(file_layout)
        
        # Program list (G-Code section)
        self.program_list = QListWidget()
        self.program_list.setMinimumHeight(200)
        self.program_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.program_list.itemDoubleClicked.connect(self.on_program_item_double_click)
        self.program_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Courier New';
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: gray;
            }
        """)
        
        # Add default program
        default_program = [
            "G01 X100 Y0 Z-550 F1000",
            "WAIT 1.0",
            "G01 X0 Y100 Z-550 F1000",
            "G01 X0 Y0 Z-550 F1000"
        ]
        self.program_list.addItems(default_program)
        
        layout.addWidget(self.program_list)

        ######################################################
        ########################################################
        
        # RED BOX - G-Code editing options (as per reference image)
        edit_group = QGroupBox("✏️ Edit G-Code")
        edit_group.setStyleSheet("""
            QGroupBox { 
                font-size: 13px; 
                font-weight: bold;
                border: 2px solid #f44336;
                border-radius: 5px;
                margin-top: 10px;
                background-color: #fff3f3;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #f44336;
            }
        """)
        edit_layout = QVBoxLayout(edit_group)
        edit_layout.setSpacing(8)
        
        # Selected line display
        selected_layout = QHBoxLayout()
        selected_layout.addWidget(QLabel("Selected:"))
        self.selected_command_label = QLabel("None")
        self.selected_command_label.setMinimumHeight(30)
        self.selected_command_label.setStyleSheet("""
            background-color: #f5f5f5;
            padding: 5px;
            border-radius: 3px;
            border: 1px solid #e0e0e0;
            font-family: 'Courier New';
            font-size: 11px;
        """)
        selected_layout.addWidget(self.selected_command_label)
        edit_layout.addLayout(selected_layout)
        
        # Edit buttons row 1
        btn_row1 = QHBoxLayout()
        
        modify_btn = QPushButton("Modify")
        modify_btn.setMinimumHeight(30)
        modify_btn.setStyleSheet("background-color: #2196f3; color: white; font-weight: bold;")
        modify_btn.clicked.connect(self.modify_selected_position)
        btn_row1.addWidget(modify_btn)
        
        insert_btn = QPushButton("Insert")
        insert_btn.setMinimumHeight(30)
        insert_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold;")
        insert_btn.clicked.connect(self.insert_new_command)
        btn_row1.addWidget(insert_btn)
        
        replace_btn = QPushButton("Replace")
        replace_btn.setMinimumHeight(30)
        replace_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        replace_btn.clicked.connect(self.replace_line)
        btn_row1.addWidget(replace_btn)
        
        edit_layout.addLayout(btn_row1)
        
        # # Edit buttons row 2
        btn_row2 = QHBoxLayout()
        
        copy_btn = QPushButton("Copy")
        copy_btn.setMinimumHeight(30)
        copy_btn.clicked.connect(self.copy_selected_line)
        btn_row2.addWidget(copy_btn)
        
        paste_btn = QPushButton("Paste")
        paste_btn.setMinimumHeight(30)
        paste_btn.clicked.connect(self.paste_line)
        btn_row2.addWidget(paste_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setMinimumHeight(30)
        delete_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        delete_btn.clicked.connect(self.delete_selected)
        btn_row2.addWidget(delete_btn)
        
        edit_layout.addLayout(btn_row2)
        
        # New values for modify
        values_layout = QHBoxLayout()
        values_layout.addWidget(QLabel("New Position:"))
        
        self.modify_x_spin = QDoubleSpinBox()
        self.modify_x_spin.setRange(-1000, 1000)
        self.modify_x_spin.setValue(0)
        self.modify_x_spin.setPrefix("X=")
        self.modify_x_spin.setMaximumWidth(90)
        values_layout.addWidget(self.modify_x_spin)
        
        self.modify_y_spin = QDoubleSpinBox()
        self.modify_y_spin.setRange(-1000, 1000)
        self.modify_y_spin.setValue(0)
        self.modify_y_spin.setPrefix("Y=")
        self.modify_y_spin.setMaximumWidth(90)
        values_layout.addWidget(self.modify_y_spin)
        
        self.modify_z_spin = QDoubleSpinBox()
        self.modify_z_spin.setRange(-1000, 0)
        self.modify_z_spin.setValue(-550)
        self.modify_z_spin.setPrefix("Z=")
        self.modify_z_spin.setMaximumWidth(90)
        values_layout.addWidget(self.modify_z_spin)
        
        values_layout.addStretch()
        edit_layout.addLayout(values_layout)
        
        layout.addWidget(edit_group)

        ######################################################
        #################################################

        # Program Control buttons
        control_group = QGroupBox("▶️ Program Control")
        control_group.setStyleSheet("QGroupBox { font-size: 13px; }")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(5)
        
        # Play button
        self.play_btn = QPushButton("PLAY")
        self.play_btn.setObjectName("play")
        self.play_btn.setMinimumHeight(35)
        self.play_btn.clicked.connect(self.play_program)
        control_layout.addWidget(self.play_btn)
        
        # Pause button
        self.pause_btn = QPushButton("PAUSE")
        self.pause_btn.setObjectName("pause")
        self.pause_btn.setMinimumHeight(35)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_program)
        control_layout.addWidget(self.pause_btn)
        
        # Reverse button
        self.reverse_btn = QPushButton("REV")
        self.reverse_btn.setObjectName("reverse")
        self.reverse_btn.setMinimumHeight(35)
        self.reverse_btn.clicked.connect(self.reverse_step)
        control_layout.addWidget(self.reverse_btn)
        
        # Forward button
        self.forward_btn = QPushButton("FWD")
        self.forward_btn.setObjectName("forward")
        self.forward_btn.setMinimumHeight(35)
        self.forward_btn.clicked.connect(self.forward_step)
        control_layout.addWidget(self.forward_btn)
        
        # Stop button
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setObjectName("stop")
        self.stop_btn.setMinimumHeight(35)
        self.stop_btn.clicked.connect(self.stop_program)
        control_layout.addWidget(self.stop_btn)
        
        layout.addWidget(control_group)
        
        # Status line
        status_layout = QHBoxLayout()
        
        status_layout.addWidget(QLabel("Line:"))
        self.current_line_label = QLabel("1")
        self.current_line_label.setStyleSheet("color: #1976d2; font-weight: bold;")
        status_layout.addWidget(self.current_line_label)
        
        status_layout.addWidget(QLabel("Status:"))
        self.program_status_label = QLabel("Stopped")
        self.program_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        status_layout.addWidget(self.program_status_label)
        
        status_layout.addStretch()
        
        status_layout.addWidget(QLabel("Total:"))
        self.total_lines_label = QLabel("4")
        self.total_lines_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.total_lines_label)
        
        layout.addLayout(status_layout)
        
        return panel
    
    def create_right_panel(self):
        """Create right panel with Position Control (Modify Position section removed)"""
        panel = QGroupBox("🎯 Position Control")
        panel.setStyleSheet("""
            QGroupBox { 
                font-size: 14px; 
                font-weight: bold;
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 15, 12, 12)
        
        # Cartesian control
        cartesian_group = QGroupBox("📐 Cartesian (XYZ)")
        cartesian_group.setStyleSheet("QGroupBox { font-size: 13px; }")
        cartesian_layout = QFormLayout(cartesian_group)
        cartesian_layout.setVerticalSpacing(10)
        cartesian_layout.setLabelAlignment(Qt.AlignRight)
        
        # X
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-1000, 1000)
        self.x_spin.setValue(0)
        self.x_spin.setSuffix(" mm")
        cartesian_layout.addRow("X:", self.x_spin)
        
        # Y
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-1000, 1000)
        self.y_spin.setValue(0)
        self.y_spin.setSuffix(" mm")
        cartesian_layout.addRow("Y:", self.y_spin)
        
        # Z
        self.z_spin = QDoubleSpinBox()
        self.z_spin.setRange(-1000, 0)
        self.z_spin.setValue(-550)
        self.z_spin.setSuffix(" mm")
        cartesian_layout.addRow("Z:", self.z_spin)
        
        # Time
        self.goto_time_spin = QDoubleSpinBox()
        self.goto_time_spin.setRange(0.1, 10.0)
        self.goto_time_spin.setValue(1.0)
        self.goto_time_spin.setSuffix(" s")
        cartesian_layout.addRow("Time:", self.goto_time_spin)
        
        layout.addWidget(cartesian_group)
        
        # GOTO button
        goto_btn = QPushButton("🚀 SEND GOTO COMMAND")
        goto_btn.setObjectName("goto")
        goto_btn.setMinimumHeight(40)
        goto_btn.clicked.connect(self.send_goto)
        layout.addWidget(goto_btn)
        
        # REMOVED: Modify Position section completely
        
        layout.addStretch()
        return panel
    
    # ===== PROGRAM MANAGEMENT METHODS =====
    
    def update_program_lines(self):
        """Update program lines list"""
        self.program_lines = []
        for i in range(self.program_list.count()):
            self.program_lines.append(self.program_list.item(i).text())
        self.total_lines_label.setText(str(self.program_list.count()))
    
    def on_program_item_double_click(self, item):
        """Handle double click on program item"""
        self.selected_command_label.setText(item.text())
        self.parse_position_from_command(item.text())
    
    def parse_position_from_command(self, command):
        """Parse X, Y, Z from command"""
        try:
            if "G01" in command or "G00" in command:
                x = extract_value(command, 'X')
                y = extract_value(command, 'Y')
                z = extract_value(command, 'Z')
                
                if x:
                    self.modify_x_spin.setValue(float(x))
                if y:
                    self.modify_y_spin.setValue(float(y))
                if z:
                    self.modify_z_spin.setValue(float(z))
        except:
            pass
    
    def modify_selected_position(self):
        """Modify selected line with new position"""
        current_row = self.program_list.currentRow()
        if current_row >= 0:
            current_text = self.program_list.item(current_row).text()
            
            new_text = current_text
            if "G01" in current_text or "G00" in current_text:
                x_val = self.modify_x_spin.value()
                y_val = self.modify_y_spin.value()
                z_val = self.modify_z_spin.value()
                
                new_text = re.sub(r'X[+-]?\d+\.?\d*', f'X{x_val}', current_text)
                new_text = re.sub(r'Y[+-]?\d+\.?\d*', f'Y{y_val}', new_text)
                new_text = re.sub(r'Z[+-]?\d+\.?\d*', f'Z{z_val}', new_text)
            
            self.program_list.item(current_row).setText(new_text)
            self.selected_command_label.setText(new_text)
            self.update_program_lines()
            
            self.log_message.emit("INFO", f"Modified line {current_row+1}: {new_text}")
    
    def insert_new_command(self):
        """Insert new command"""
        current_row = self.program_list.currentRow()
        x = self.modify_x_spin.value()
        y = self.modify_y_spin.value()
        z = self.modify_z_spin.value()
        
        new_command = f"G01 X{x} Y{y} Z{z} F1000"
        
        if current_row >= 0:
            self.program_list.insertItem(current_row + 1, new_command)
            self.program_list.setCurrentRow(current_row + 1)
        else:
            self.program_list.addItem(new_command)
            self.program_list.setCurrentRow(self.program_list.count() - 1)
        
        self.selected_command_label.setText(new_command)
        self.update_program_lines()
        self.log_message.emit("INFO", f"Inserted: {new_command}")
    
    def copy_selected_line(self):
        """Copy selected line to clipboard"""
        current_row = self.program_list.currentRow()
        if current_row >= 0:
            text = self.program_list.item(current_row).text()
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.log_message.emit("INFO", "Line copied to clipboard")
    
    def paste_line(self):
        """Paste from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            current_row = self.program_list.currentRow()
            if current_row >= 0:
                self.program_list.insertItem(current_row + 1, text)
                self.program_list.setCurrentRow(current_row + 1)
            else:
                self.program_list.addItem(text)
                self.program_list.setCurrentRow(self.program_list.count() - 1)
            
            self.selected_command_label.setText(text)
            self.update_program_lines()
            self.log_message.emit("INFO", "Pasted from clipboard")
    
    def replace_line(self):
        """Replace current line with new command"""
        current_row = self.program_list.currentRow()
        if current_row >= 0:
            x = self.modify_x_spin.value()
            y = self.modify_y_spin.value()
            z = self.modify_z_spin.value()
            
            new_command = f"G01 X{x} Y{y} Z{z} F1000"
            
            self.program_list.item(current_row).setText(new_command)
            self.selected_command_label.setText(new_command)
            self.update_program_lines()
            self.log_message.emit("INFO", f"Replaced line {current_row+1}")
    
    def move_j(self):
        """Move J command"""
        self.log_message.emit("INFO", "Move J command sent")
        # Add your Move J logic here
    
    def return_to_home(self):
        """Return to home position"""
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self.z_spin.setValue(-550)
        self.send_goto()
        self.log_message.emit("INFO", "Returning to home position")
    
    def reload_program(self):
        """Reload current program"""
        # Save current program temporarily
        temp_lines = []
        for i in range(self.program_list.count()):
            temp_lines.append(self.program_list.item(i).text())
        
        # Clear and reload
        self.program_list.clear()
        self.program_list.addItems(temp_lines)
        self.update_program_lines()
        self.log_message.emit("INFO", "Program reloaded")
    
    def play_program(self):
        """Play program - FIXED VERSION"""
        if self.program_list.count() == 0:
            QMessageBox.warning(self, "No Program", "No program loaded!")
            return
        
        if not self.connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to controller first!")
            return
        
        self.program_running = True
        self.program_paused = False
        self.current_line = 0
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        
        self.program_status_label.setText("Running")
        self.program_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        self.current_line_label.setText("1")
        self.highlight_current_line()
        
        # Start execution from first line
        self.execute_current_line()
    
    def pause_program(self):
        """Pause program"""
        self.program_running = False
        self.program_paused = True
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.program_status_label.setText("Paused")
        self.program_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
    
    def stop_program(self):
        """Stop program"""
        self.program_running = False
        self.program_paused = False
        self.current_line = 0
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.program_status_label.setText("Stopped")
        self.program_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        self.current_line_label.setText("1")
        self.highlight_current_line()
    
    def reverse_step(self):
        """Execute previous line"""
        if self.program_list.count() == 0:
            return
        
        if self.current_line > 0:
            self.current_line -= 1
            self.current_line_label.setText(str(self.current_line + 1))
            self.highlight_current_line()
            
            # Execute current line
            self.execute_current_line()
    
    def forward_step(self):
        """Execute next line"""
        if self.program_list.count() == 0:
            return
        
        if self.current_line < self.program_list.count() - 1:
            self.current_line += 1
            self.current_line_label.setText(str(self.current_line + 1))
            self.highlight_current_line()
            
            # Execute current line
            self.execute_current_line()
    
    def execute_current_line(self):
        """Execute current line - FIXED: Actually sends command"""
        if self.current_line < self.program_list.count():
            command = self.program_list.item(self.current_line).text()
            
            # Send command to Arduino via signal
            self.program_command.emit(command)
            
            # Log for debugging
            self.log_message.emit("INFO", f"Executing: {command}")
            print(f"Sending command: {command}")  # Debug print
            
            # If program is running automatically, schedule next line
            if self.program_running and not self.program_paused:
                if self.current_line < self.program_list.count() - 1:
                    QTimer.singleShot(45, self.execute_next_line)
                else:
                    # Program complete
                    self.program_running = False
                    self.play_btn.setEnabled(True)
                    self.pause_btn.setEnabled(False)
                    self.program_status_label.setText("Complete")
                    self.program_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
    
    def execute_next_line(self):
        """Execute next line - FIXED: Properly handles progression"""
        if not self.program_running or self.program_paused:
            return
        
        if self.current_line < self.program_list.count() - 1:
            self.current_line += 1
            self.current_line_label.setText(str(self.current_line + 1))
            self.highlight_current_line()
            
            # Execute the new current line
            self.execute_current_line()
        else:
            # Program complete
            self.program_running = False
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.program_status_label.setText("Complete")
            self.program_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
    
    def highlight_current_line(self):
        """Highlight current line"""
        for i in range(self.program_list.count()):
            item = self.program_list.item(i)
            if i == self.current_line:
                item.setBackground(QColor(227, 242, 253))  # Light blue
                item.setForeground(QColor(25, 118, 210))  # Dark blue
            else:
                item.setBackground(QColor(255, 255, 255))
                item.setForeground(QColor(51, 51, 51))
    
    def new_program(self):
        """Create new program"""
        self.program_list.clear()
        self.program_label.setText("📄 New Program")
        self.current_line = 0
        self.current_line_label.setText("1")
        self.update_program_lines()
    
    def load_program(self):
        """Load program from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Program", "", "Program Files (*.txt *.gcode *.nc);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                self.program_list.clear()
                self.program_list.addItems([line.strip() for line in lines if line.strip()])
                self.program_label.setText(f"📄 {file_path.split('/')[-1]}")
                self.update_program_lines()
                self.current_line = 0
                self.current_line_label.setText("1")
            except Exception as e:
                print(f"Error loading: {e}")
    
    def save_program(self):
        """Save program to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Program", "", "Program Files (*.txt *.gcode *.nc);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    for i in range(self.program_list.count()):
                        f.write(self.program_list.item(i).text() + "\n")
                self.program_label.setText(f"📄 {file_path.split('/')[-1]}")
            except Exception as e:
                print(f"Error saving: {e}")
    
    def teach_position(self):
        """Teach current position"""
        x = self.x_spin.value()
        y = self.y_spin.value()
        z = self.z_spin.value()
        
        position = f"G01 X{x} Y{y} Z{z} F1000"
        self.program_list.addItem(position)
        self.program_list.setCurrentRow(self.program_list.count() - 1)
        self.selected_command_label.setText(position)
        self.update_program_lines()
    
    def delete_selected(self):
        """Delete selected line"""
        current_row = self.program_list.currentRow()
        if current_row >= 0:
            self.program_list.takeItem(current_row)
            self.selected_command_label.setText("None")
            self.update_program_lines()
            
            # Adjust current line if needed
            if self.current_line >= self.program_list.count():
                self.current_line = max(0, self.program_list.count() - 1)
                self.current_line_label.setText(str(self.current_line + 1))
    
    def send_goto(self):
        """Send GOTO command"""
        x = self.x_spin.value()
        y = self.y_spin.value()
        z = self.z_spin.value()
        time_val = self.goto_time_spin.value()
        
        self.goto_command.emit(x, y, z, time_val)
        self.log_message.emit("INFO", f"GOTO: X{x} Y{y} Z{z} Time:{time_val}")
    
    def set_connection_status(self, connected):
        """Update connection status"""
        self.connected = connected
        if connected:
            self.conn_status_label.setText("● Connected")
            self.conn_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            self.conn_status_label.setText("● Disconnected")
            self.conn_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
    
    def _handle_log(self, level, message):
        """Handle log messages internally"""
        # Just print for now
        print(f"[{level}] {message}")