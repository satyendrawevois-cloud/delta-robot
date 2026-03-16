from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class ThemeManager:
    """Theme manager for light/dark mode"""
    
    LIGHT = "light"
    DARK = "dark"
    
    @staticmethod
    def get_light_palette():
        """Get light theme palette"""
        palette = QPalette()
        
        # Base colors - Professional light theme
        palette.setColor(QPalette.Window, QColor(240, 240, 245))  # Soft gray-blue
        palette.setColor(QPalette.WindowText, QColor(40, 40, 50))  # Dark blue-gray
        palette.setColor(QPalette.Base, QColor(255, 255, 255))  # Pure white
        palette.setColor(QPalette.AlternateBase, QColor(250, 250, 252))  # Off-white
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(40, 40, 50))
        palette.setColor(QPalette.Text, QColor(40, 40, 50))
        palette.setColor(QPalette.Button, QColor(245, 245, 250))  # Light gray-blue
        palette.setColor(QPalette.ButtonText, QColor(40, 40, 50))
        palette.setColor(QPalette.BrightText, QColor(220, 60, 60))
        palette.setColor(QPalette.Link, QColor(0, 105, 180))  # Professional blue
        palette.setColor(QPalette.Highlight, QColor(0, 120, 210))  # Bright blue
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # Disabled states
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 160))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 160))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(150, 150, 160))
        
        return palette
    
    @staticmethod
    def get_dark_palette():
        """Get dark theme palette - Professional dark theme"""
        palette = QPalette()
        
        # Base colors - Professional dark theme
        palette.setColor(QPalette.Window, QColor(30, 35, 45))  # Deep blue-gray
        palette.setColor(QPalette.WindowText, QColor(220, 225, 235))  # Light gray
        palette.setColor(QPalette.Base, QColor(40, 45, 55))  # Slightly lighter
        palette.setColor(QPalette.AlternateBase, QColor(35, 40, 50))
        palette.setColor(QPalette.ToolTipBase, QColor(50, 55, 65))
        palette.setColor(QPalette.ToolTipText, QColor(220, 225, 235))
        palette.setColor(QPalette.Text, QColor(220, 225, 235))
        palette.setColor(QPalette.Button, QColor(45, 50, 60))
        palette.setColor(QPalette.ButtonText, QColor(220, 225, 235))
        palette.setColor(QPalette.BrightText, QColor(255, 100, 100))
        palette.setColor(QPalette.Link, QColor(80, 160, 255))  # Bright blue
        palette.setColor(QPalette.Highlight, QColor(0, 120, 210))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # Disabled states
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 110, 120))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 110, 120))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(100, 110, 120))
        
        return palette
    
    @staticmethod
    def get_stylesheet(theme="light"):
        """Get stylesheet based on theme"""
        
        if theme == "dark":
            return """
            /* ========== DARK THEME - PROFESSIONAL ========== */
            QMainWindow, QDialog, QWidget {
                background-color: #1e232f;
                color: #e0e5f0;
            }
            
            /* ===== MENU BAR ===== */
            QMenuBar {
                background-color: #252b38;
                color: #e0e5f0;
                border-bottom: 2px solid #2f3a5c;
                font-weight: 500;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                margin: 2px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #2f3a5c;
                color: #80b0ff;
            }
            QMenuBar::item:pressed {
                background-color: #3a4668;
            }
            
            /* ===== MENU ===== */
            QMenu {
                background-color: #2a3142;
                color: #e0e5f0;
                border: 1px solid #3a4668;
                border-radius: 5px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #2f3a5c;
                color: #80b0ff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3a4668;
                margin: 4px 0;
            }
            
            /* ===== TOOLBAR ===== */
            QToolBar {
                background-color: #252b38;
                border: none;
                border-bottom: 2px solid #2f3a5c;
                spacing: 8px;
                padding: 6px;
            }
            QToolBar QPushButton {
                background-color: #2f3a5c;
                border: 1px solid #3e4b70;
                border-radius: 5px;
                padding: 8px 15px;
                color: #e0e5f0;
                font-weight: 500;
            }
            QToolBar QPushButton:hover {
                background-color: #3e4b70;
                border-color: #5a6b99;
            }
            QToolBar QPushButton:pressed {
                background-color: #1e232f;
            }
            
            /* ===== TAB WIDGET ===== */
            QTabWidget::pane {
                background-color: #1e232f;
                border: 2px solid #2f3a5c;
                border-radius: 8px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #252b38;
                color: #a0a8b8;
                border: 2px solid #2f3a5c;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 25px;
                margin-right: 2px;
                font-weight: 600;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #1e232f;
                color: #80b0ff;
                border-bottom: 2px solid #1e232f;
                margin-bottom: -2px;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2f3a5c;
                color: #e0e5f0;
            }
            
            /* ===== GROUP BOXES ===== */
            QGroupBox {
                background-color: #252b38;
                border: 2px solid #2f3a5c;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
                color: #e0e5f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #80b0ff;
                font-size: 14px;
            }
            
            /* ===== PUSH BUTTONS ===== */
            QPushButton {
                background-color: #2f3a5c;
                border: 1px solid #3e4b70;
                border-radius: 5px;
                padding: 8px 15px;
                color: #e0e5f0;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3e4b70;
                border-color: #5a6b99;
            }
            QPushButton:pressed {
                background-color: #1e232f;
            }
            QPushButton:checked {
                background-color: #4caf50;
                border-color: #66bb6a;
                color: white;
            }
            QPushButton:disabled {
                background-color: #2a3142;
                border-color: #3a3f4e;
                color: #808080;
            }
            
            /* Special buttons */
            QPushButton#emergency {
                background-color: #d32f2f;
                border: 1px solid #b71c1c;
                color: white;
                font-weight: bold;
            }
            QPushButton#emergency:hover {
                background-color: #f44336;
            }
            QPushButton#play {
                background-color: #2e7d32;
                border: 1px solid #1b5e20;
                color: white;
            }
            QPushButton#pause {
                background-color: #ef6c00;
                border: 1px solid #e65100;
                color: white;
            }
            QPushButton#reverse, QPushButton#forward {
                background-color: #1565c0;
                border: 1px solid #0d47a1;
                color: white;
            }
            QPushButton#connect_btn {
                background-color: #2e7d32;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#connect_btn:checked {
                background-color: #c62828;
            }
            QPushButton#calibrate_btn {
                background-color: #ef6c00;
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
            
            /* ===== INPUT FIELDS ===== */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #1e232f;
                border: 2px solid #2f3a5c;
                border-radius: 5px;
                padding: 8px;
                color: #e0e5f0;
                selection-background-color: blue;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #80b0ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #80b0ff;
                margin-right: 5px;
            }
            
            /* ===== LIST WIDGETS ===== */
            QListWidget {
                background-color: #1e232f;
                border: 2px solid #2f3a5c;
                border-radius: 6px;
                color: #e0e5f0;
                outline: none;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2f3a5c;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #2f3a5c;
                color: #80b0ff;
            }
            QListWidget::item:hover {
                background-color: #2a3142;
            }
            
            /* ===== TEXT EDIT ===== */
            QTextEdit {
                background-color: #1a1e2a;
                border: 2px solid #2f3a5c;
                border-radius: 6px;
                color: #00ff9d;
                font-family: 'Courier New';
                padding: 8px;
            }
            
            /* ===== LABELS ===== */
            QLabel {
                color: #e0e5f0;
                background-color: transparent;
            }
            
            /* ===== STATUS BAR ===== */
            QStatusBar {
                background-color: #252b38;
                color: #80b0ff;
                border-top: 2px solid #2f3a5c;
                padding: 5px;
                font-weight: 500;
            }
            
            /* ===== SCROLL BARS ===== */
            QScrollBar:vertical {
                background-color: #1e232f;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #2f3a5c;
                border-radius: 7px;
                min-height: 25px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3e4b70;
            }
            QScrollBar:horizontal {
                background-color: #1e232f;
                height: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background-color: #2f3a5c;
                border-radius: 7px;
                min-width: 25px;
            }
            
            /* ===== CHECK BOXES ===== */
            QCheckBox {
                color: #e0e5f0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #2f3a5c;
                border-radius: 4px;
                background-color: #1e232f;
            }
            QCheckBox::indicator:checked {
                background-color: #4caf50;
                border-color: #66bb6a;
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='white'><path d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/></svg>");
            }
            
            /* ===== PROGRESS BAR ===== */
            QProgressBar {
                border: 2px solid #2f3a5c;
                border-radius: 5px;
                text-align: center;
                color: #e0e5f0;
                background-color: #1e232f;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
            
            /* ===== TOOLTIPS ===== */
            QToolTip {
                background-color: #2a3142;
                color: #e0e5f0;
                border: 1px solid #3e4b70;
                border-radius: 3px;
                padding: 5px;
            }
            """
        else:
            return """
            /* ========== LIGHT THEME - PROFESSIONAL ========== */
            QMainWindow, QDialog, QWidget {
                background-color: #f0f2f7;
                color: #1a2639;
            }
            
            /* ===== MENU BAR ===== */
            QMenuBar {
                background-color: #ffffff;
                color: #1a2639;
                border-bottom: 2px solid #d0d7e8;
                font-weight: 500;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                margin: 2px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            
            /* ===== MENU ===== */
            QMenu {
                background-color: #ffffff;
                color: #1a2639;
                border: 1px solid #d0d7e8;
                border-radius: 5px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QMenu::separator {
                height: 1px;
                background-color: #d0d7e8;
                margin: 4px 0;
            }
            
            /* ===== TOOLBAR ===== */
            QToolBar {
                background-color: #ffffff;
                border: none;
                border-bottom: 2px solid #d0d7e8;
                spacing: 8px;
                padding: 6px;
            }
            QToolBar QPushButton {
                background-color: #f0f2f7;
                border: 1px solid #d0d7e8;
                border-radius: 5px;
                padding: 8px 15px;
                color: #1a2639;
                font-weight: 500;
            }
            QToolBar QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #1976d2;
            }
            
            /* ===== TAB WIDGET ===== */
            QTabWidget::pane {
                background-color: #ffffff;
                border: 2px solid #d0d7e8;
                border-radius: 8px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #f0f2f7;
                color: #5a6b7a;
                border: 2px solid #d0d7e8;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 25px;
                margin-right: 2px;
                font-weight: 600;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1976d2;
                border-bottom: 2px solid #ffffff;
                margin-bottom: -2px;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            
            /* ===== GROUP BOXES ===== */
            QGroupBox {
                background-color: #ffffff;
                border: 2px solid #d0d7e8;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
                color: #1a2639;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #1976d2;
                font-size: 14px;
            }
            
            /* ===== PUSH BUTTONS ===== */
            QPushButton {
                background-color: #f0f2f7;
                border: 1px solid #d0d7e8;
                border-radius: 5px;
                padding: 8px 15px;
                color: #1a2639;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #bbdefb;
            }
            QPushButton:checked {
                background-color: #4caf50;
                border-color: #45a049;
                color: white;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                border-color: #e0e0e0;
                color: #bdbdbd;
            }
            
            /* Special buttons */
            QPushButton#emergency {
                background-color: #f44336;
                border: 1px solid #d32f2f;
                color: white;
            }
            QPushButton#play {
                background-color: #4caf50;
                color: white;
            }
            QPushButton#pause {
                background-color: #ff9800;
                color: white;
            }
            QPushButton#reverse, QPushButton#forward {
                background-color: #2196f3;
                color: white;
            }
            QPushButton#connect_btn {
                background-color: #4caf50;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#connect_btn:checked {
                background-color: #f44336;
            }
            QPushButton#calibrate_btn {
                background-color: #ff9800;
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
            
            /* ===== INPUT FIELDS ===== */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #ffffff;
                border: 2px solid #d0d7e8;
                border-radius: 5px;
                padding: 8px;
                color: #1a2639;
                selection-background-color: blue;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #1976d2;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #1976d2;
                margin-right: 5px;
            }
            
            /* ===== LIST WIDGETS ===== */
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #d0d7e8;
                border-radius: 6px;
                color: #1a2639;
                outline: none;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e7f0;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            
            /* ===== TEXT EDIT ===== */
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #d0d7e8;
                border-radius: 6px;
                color: #1a2639;
                font-family: 'Courier New';
                padding: 8px;
            }
            
            /* ===== LABELS ===== */
            QLabel {
                color: #1a2639;
                background-color: transparent;
            }
            
            /* ===== STATUS BAR ===== */
            QStatusBar {
                background-color: #ffffff;
                color: #1976d2;
                border-top: 2px solid #d0d7e8;
                padding: 5px;
                font-weight: 500;
            }
            
            /* ===== SCROLL BARS ===== */
            QScrollBar:vertical {
                background-color: #f0f2f7;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c8d8;
                border-radius: 7px;
                min-height: 25px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a8c0;
            }
            
            /* ===== CHECK BOXES ===== */
            QCheckBox {
                color: #1a2639;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #d0d7e8;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #4caf50;
                border-color: #45a049;
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='white'><path d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/></svg>");
            }
            
            /* ===== TOOLTIPS ===== */
            QToolTip {
                background-color: #ffffff;
                color: #1a2639;
                border: 1px solid #d0d7e8;
                border-radius: 3px;
                padding: 5px;
            }
            """