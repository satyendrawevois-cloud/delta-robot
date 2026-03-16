from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal
from utils import get_timestamp

class LogTab(QWidget):
    """System Log Tab"""
    
    # Define signal for adding logs
    log_added = pyqtSignal(str, str)  # level, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.log_added.connect(self._add_log_to_display)  # Connect signal to slot
        self.add_log("INFO", "System Log initialized")
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier New", 9))
        self.log_display.setMinimumHeight(200)
        layout.addWidget(self.log_display)
        
        # Log controls
        controls_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.clear_log)
        controls_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("Save Log")
        save_btn.clicked.connect(self.save_log)
        controls_layout.addWidget(save_btn)
        
        controls_layout.addStretch()
        
        # Log level
        controls_layout.addWidget(QLabel("Log Level:"))
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText("INFO")
        controls_layout.addWidget(self.log_level)
        
        layout.addLayout(controls_layout)
    
    def add_log(self, level, message):
        """Public method to add log - emits signal"""
        self.log_added.emit(level, message)
    
    def _add_log_to_display(self, level, message):
        """Private slot to actually add log to display"""
        timestamp = get_timestamp()
        
        # Color coding based on level
        colors = {
            "ERROR": "#f44336",
            "WARNING": "#ff9800", 
            "DEBUG": "#2196f3",
            "INFO": "#4caf50"
        }
        color = colors.get(level, "#ffffff")
        
        # Check log level filter
        current_level = self.log_level.currentText()
        level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        if level_priority.get(level, 1) < level_priority.get(current_level, 1):
            return  # Skip if below current log level
        
        log_entry = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span><br>'
        self.log_display.insertHtml(log_entry)
        
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
    
    def clear_log(self):
        """Clear log display"""
        self.log_display.clear()
        self.add_log("INFO", "Log cleared")
    
    def save_log(self):
        """Save log to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "", "Log Files (*.log *.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_display.toPlainText())
                self.add_log("INFO", f"Log saved: {file_path}")
            except Exception as e:
                self.add_log("ERROR", f"Failed to save log: {str(e)}")