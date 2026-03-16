from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import numpy as np
import json
from datetime import datetime
import os
import time

class VisionTab(QWidget):
    """Vision System Tab with Exact Layout - FIXED"""
    
    log_message = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.camera_running = False
        self.camera = None
        self.current_frame = None
        self.captured_image = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        self.init_ui()
        self.setup_connections()
        self.detect_available_cameras()
        
    def init_ui(self):
        """Initialize the vision tab UI with exact layout"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # ===== LEFT COLUMN =====
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(self.create_camera_section())
        left_layout.addWidget(self.create_snap_teach_section())
        left_layout.addWidget(self.create_all_settings_section())
        
        left_layout.addStretch()
        main_layout.addWidget(left_column, 25)
        
        # ===== CENTER COLUMN =====
        center_column = QWidget()
        center_layout = QVBoxLayout(center_column)
        center_layout.setSpacing(5)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        center_layout.addWidget(self.create_origin_section())
        center_layout.addWidget(self.create_all_values_section())
        
        center_layout.addStretch()
        main_layout.addWidget(center_column, 35)
        
        # ===== RIGHT COLUMN =====
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_layout.addWidget(self.create_video_feed_section())
        right_layout.addWidget(self.create_save_button())
        
        main_layout.addWidget(right_column, 40)
    
    def create_camera_section(self):
        """HP HD Camera Section"""
        group = QGroupBox("HP HD Camera")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 3px 0 3px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("Camera 0")
        layout.addWidget(self.camera_combo)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        
        self.start_camera_btn = QPushButton("Start Camera")
        self.start_camera_btn.setStyleSheet("QPushButton { background-color: #4caf50; color: white; padding: 3px; }")
        self.start_camera_btn.clicked.connect(self.start_camera)
        btn_layout.addWidget(self.start_camera_btn)
        
        self.stop_camera_btn = QPushButton("Stop Camera")
        self.stop_camera_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 3px; }")
        self.stop_camera_btn.clicked.connect(self.stop_camera)
        self.stop_camera_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_camera_btn)
        
        layout.addLayout(btn_layout)
        
        return group
    
    def create_snap_teach_section(self):
        """Snap Image & Teach Object Section"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        snap_btn = QPushButton("Snap Image")
        snap_btn.clicked.connect(self.snap_image)
        layout.addWidget(snap_btn)
        
        teach_btn = QPushButton("Teach Object")
        teach_btn.clicked.connect(self.teach_object)
        layout.addWidget(teach_btn)
        
        return widget
    
    def create_all_settings_section(self):
        """All Settings Section with Zoom, Brightness, Contrast, etc"""
        group = QGroupBox("All Settings")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # Row 1: Zoom
        layout.addWidget(QLabel("Zoom:"), 0, 0)
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(0.1, 10.0)
        self.zoom_spin.setValue(1.0)
        self.zoom_spin.setSingleStep(0.1)
        layout.addWidget(self.zoom_spin, 0, 1)
        
        # Row 1: Brightness
        layout.addWidget(QLabel("Brightness:"), 0, 2)
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 200)
        self.brightness_slider.setValue(100)
        layout.addWidget(self.brightness_slider, 0, 3)
        
        # Row 2: Contrast
        layout.addWidget(QLabel("Contrast:"), 1, 0)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 200)
        self.contrast_slider.setValue(100)
        layout.addWidget(self.contrast_slider, 1, 1, 1, 3)
        
        # Row 3: Select Object
        layout.addWidget(QLabel("Select Object:"), 2, 0)
        self.object_combo = QComboBox()
        self.object_combo.addItems(["Object 1", "Object 2", "Object 3"])
        layout.addWidget(self.object_combo, 2, 1)
        
        # Row 3: Color
        self.color_edit = QLineEdit("45, 45, 45")
        self.color_edit.setFixedWidth(70)
        layout.addWidget(self.color_edit, 2, 2)
        
        auto_btn = QPushButton("Auto")
        auto_btn.setMaximumWidth(40)
        auto_btn.clicked.connect(self.auto_background)
        layout.addWidget(auto_btn, 2, 3)
        
        # Row 4: Background Color
        layout.addWidget(QLabel("Background Color:"), 3, 0, 1, 2)
        
        # Row 4: Score Threshold
        layout.addWidget(QLabel("Score Threshold:"), 3, 2)
        self.score_threshold = QDoubleSpinBox()
        self.score_threshold.setRange(0, 100)
        self.score_threshold.setValue(80.0)
        layout.addWidget(self.score_threshold, 3, 3)
        
        return group
    
    def create_origin_section(self):
        """ORIGIN (X1,Y1) Section"""
        group = QGroupBox("ORIGIN (X1,Y1)")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ff9800;
                border-radius: 3px;
            }
            QGroupBox::title {
                color: #ff9800;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("X:"))
        self.origin_x = QLineEdit("0.0")
        self.origin_x.setReadOnly(True)
        coord_layout.addWidget(self.origin_x)
        
        coord_layout.addWidget(QLabel("Y:"))
        self.origin_y = QLineEdit("0.0")
        self.origin_y.setReadOnly(True)
        coord_layout.addWidget(self.origin_y)
        
        set_btn = QPushButton("Set")
        set_btn.setMaximumWidth(40)
        set_btn.clicked.connect(self.set_origin)
        coord_layout.addWidget(set_btn)
        
        layout.addLayout(coord_layout)
        
        return group
    
    def create_all_values_section(self):
        """ALL VALUES Section"""
        group = QGroupBox("ALL VALUES")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QHBoxLayout(group)
        layout.setSpacing(5)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # FOUND VALUES
        found_group = QGroupBox("FOUND VALUES")
        found_group.setStyleSheet("QGroupBox { font-size: 10px; }")
        found_layout = QGridLayout(found_group)
        found_layout.setSpacing(1)
        found_layout.setContentsMargins(2, 2, 2, 2)
        
        found_layout.addWidget(QLabel("Scored Value:"), 0, 0)
        self.scored_value = QLineEdit("1.0")
        self.scored_value.setFixedWidth(50)
        found_layout.addWidget(self.scored_value, 0, 1)
        
        found_layout.addWidget(QLabel("X1 Pixel Pos:"), 1, 0)
        self.x1_pixel_found = QLineEdit("1.0")
        self.x1_pixel_found.setFixedWidth(50)
        found_layout.addWidget(self.x1_pixel_found, 1, 1)
        
        found_layout.addWidget(QLabel("Y1 Robot Pos:"), 1, 2)
        self.y1_robot_found = QLineEdit("1.0")
        self.y1_robot_found.setFixedWidth(50)
        found_layout.addWidget(self.y1_robot_found, 1, 3)
        
        found_layout.addWidget(QLabel("Found Angle:"), 2, 0)
        self.found_angle = QLineEdit("1.0")
        self.found_angle.setFixedWidth(50)
        found_layout.addWidget(self.found_angle, 2, 1)
        
        found_layout.addWidget(QLabel("X2 Pixel Pos:"), 2, 2)
        self.x2_pixel_found = QLineEdit("1.0")
        self.x2_pixel_found.setFixedWidth(50)
        found_layout.addWidget(self.x2_pixel_found, 2, 3)
        
        found_layout.addWidget(QLabel("Pixel X Pos:"), 3, 0)
        self.pixel_x_found = QLineEdit("1.0")
        self.pixel_x_found.setFixedWidth(50)
        found_layout.addWidget(self.pixel_x_found, 3, 1)
        
        found_layout.addWidget(QLabel("Y2 Pixel Pos:"), 3, 2)
        self.y2_pixel_found = QLineEdit("1.0")
        self.y2_pixel_found.setFixedWidth(50)
        found_layout.addWidget(self.y2_pixel_found, 3, 3)
        
        found_layout.addWidget(QLabel("Robot X Pos:"), 4, 0)
        self.robot_x_found = QLineEdit("1.0")
        self.robot_x_found.setFixedWidth(50)
        found_layout.addWidget(self.robot_x_found, 4, 1)
        
        found_layout.addWidget(QLabel("Robot Y Pos:"), 4, 2)
        self.robot_y_found = QLineEdit("1.0")
        self.robot_y_found.setFixedWidth(50)
        found_layout.addWidget(self.robot_y_found, 4, 3)
        
        layout.addWidget(found_group)
        
        # CALIBRATION VALUES
        calib_group = QGroupBox("CALIBRATION VALUES")
        calib_group.setStyleSheet("QGroupBox { font-size: 10px; }")
        calib_layout = QGridLayout(calib_group)
        calib_layout.setSpacing(1)
        calib_layout.setContentsMargins(2, 2, 2, 2)
        
        calib_layout.addWidget(QLabel("Scored Value:"), 0, 0)
        self.calib_scored = QLineEdit("1.0")
        self.calib_scored.setFixedWidth(50)
        calib_layout.addWidget(self.calib_scored, 0, 1)
        
        calib_layout.addWidget(QLabel("X1 Pixel Pos:"), 1, 0)
        self.x1_pixel_calib = QLineEdit("1.0")
        self.x1_pixel_calib.setFixedWidth(50)
        calib_layout.addWidget(self.x1_pixel_calib, 1, 1)
        
        calib_layout.addWidget(QLabel("Y1 Robot Pos:"), 1, 2)
        self.y1_robot_calib = QLineEdit("1.0")
        self.y1_robot_calib.setFixedWidth(50)
        calib_layout.addWidget(self.y1_robot_calib, 1, 3)
        
        calib_layout.addWidget(QLabel("Found Angle:"), 2, 0)
        self.calib_angle = QLineEdit("1.0")
        self.calib_angle.setFixedWidth(50)
        calib_layout.addWidget(self.calib_angle, 2, 1)
        
        calib_layout.addWidget(QLabel("X2 Pixel Pos:"), 2, 2)
        self.x2_pixel_calib = QLineEdit("1.0")
        self.x2_pixel_calib.setFixedWidth(50)
        calib_layout.addWidget(self.x2_pixel_calib, 2, 3)
        
        calib_layout.addWidget(QLabel("Pixel X Pos:"), 3, 0)
        self.pixel_x_calib = QLineEdit("1.0")
        self.pixel_x_calib.setFixedWidth(50)
        calib_layout.addWidget(self.pixel_x_calib, 3, 1)
        
        calib_layout.addWidget(QLabel("Y2 Pixel Pos:"), 3, 2)
        self.y2_pixel_calib = QLineEdit("1.0")
        self.y2_pixel_calib.setFixedWidth(50)
        calib_layout.addWidget(self.y2_pixel_calib, 3, 3)
        
        calib_layout.addWidget(QLabel("Robot X Pos:"), 4, 0)
        self.robot_x_calib = QLineEdit("1.0")
        self.robot_x_calib.setFixedWidth(50)
        calib_layout.addWidget(self.robot_x_calib, 4, 1)
        
        calib_layout.addWidget(QLabel("Robot Y Pos:"), 4, 2)
        self.robot_y_calib = QLineEdit("1.0")
        self.robot_y_calib.setFixedWidth(50)
        calib_layout.addWidget(self.robot_y_calib, 4, 3)
        
        layout.addWidget(calib_group)
        
        return group
    
    def create_video_feed_section(self):
        """LIVE VIDEO FEED Section"""
        group = QGroupBox("LIVE VIDEO FEED")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4caf50;
                border-radius: 3px;
            }
            QGroupBox::title {
                color: #4caf50;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.video_label = QLabel()
        self.video_label.setMinimumSize(400, 300)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #333;
                color: #888;
            }
        """)
        self.video_label.setText("Camera not started")
        layout.addWidget(self.video_label)
        
        return group
    
    def create_save_button(self):
        """SAVE VISION DATA Button"""
        save_btn = QPushButton("SAVE VISION DATA")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_vision_data)
        return save_btn
    
    def setup_connections(self):
        """Setup signal/slot connections"""
        self.log_message.connect(self._handle_log)
    
    def detect_available_cameras(self):
        """Detect available cameras"""
        self.camera_combo.clear()
        available_cameras = []
        
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        if available_cameras:
            for cam in available_cameras:
                self.camera_combo.addItem(f"Camera {cam}", cam)
        else:
            self.camera_combo.addItem("No cameras found", -1)
    
    def start_camera(self):
        """Start camera capture - FIXED"""
        try:
            camera_index = self.camera_combo.currentData()
            if camera_index < 0:
                QMessageBox.warning(self, "Camera Error", "No valid camera selected!")
                return
            
            # Release existing camera
            if self.camera:
                self.camera.release()
            
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                QMessageBox.warning(self, "Camera Error", "Could not open camera!")
                return
            
            # Allow camera to warm up
            QThread.msleep(200)
            
            # Set properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Test read
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                QMessageBox.warning(self, "Camera Error", "Camera not sending frames!")
                self.camera.release()
                self.camera = None
                return
            
            print(f"Camera started - Frame shape: {test_frame.shape}")
            
            self.camera_running = True
            self.start_camera_btn.setEnabled(False)
            self.stop_camera_btn.setEnabled(True)
            self.timer.start(30)  # ~33 fps
            
            self.log_message.emit("INFO", "Camera started successfully")
            
        except Exception as e:
            print(f"Camera error: {str(e)}")
            QMessageBox.critical(self, "Camera Error", f"Error: {str(e)}")
    
    def stop_camera(self):
        """Stop camera capture"""
        self.timer.stop()
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_running = False
        self.start_camera_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(False)
        self.video_label.setText("Camera stopped")
        self.video_label.setPixmap(QPixmap())
        
        self.log_message.emit("INFO", "Camera stopped")
    
    def update_frame(self):
        """Update video frame - FIXED"""
        if self.camera and self.camera.isOpened():
            try:
                ret, frame = self.camera.read()
                if ret and frame is not None and frame.size > 0:
                    self.current_frame = frame.copy()
                    
                    # Apply brightness and contrast
                    brightness = self.brightness_slider.value() - 100
                    contrast = self.contrast_slider.value() / 100.0
                    
                    frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
                    
                    # Convert BGR to RGB
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Get image dimensions
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    
                    # Create QImage from numpy array
                    # Using a direct buffer approach
                    q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    
                    # Create a deep copy to ensure data persistence
                    q_image_deep = q_image.copy()
                    
                    if not q_image_deep.isNull():
                        pixmap = QPixmap.fromImage(q_image_deep)
                        scaled_pixmap = pixmap.scaled(
                            self.video_label.size(), 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                        self.video_label.setPixmap(scaled_pixmap)
                    else:
                        print("QImage is null")
                        
            except Exception as e:
                print(f"Frame update error: {str(e)}")
    
    def snap_image(self):
        """Snap image"""
        if self.current_frame is not None:
            filename = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            cv2.imwrite(filename, self.current_frame)
            self.log_message.emit("INFO", f"Image saved: {filename}")
            QMessageBox.information(self, "Snap Image", f"Image saved as {filename}")
    
    def teach_object(self):
        """Teach object"""
        if self.current_frame is None:
            QMessageBox.warning(self, "No Image", "Please start camera first!")
            return
        
        object_name = self.object_combo.currentText()
        self.log_message.emit("INFO", f"Object '{object_name}' taught")
        QMessageBox.information(self, "Teach Object", f"Object '{object_name}' has been taught!")
    
    def auto_background(self):
        """Auto detect background color"""
        if self.current_frame is not None:
            h, w = self.current_frame.shape[:2]
            top = np.mean(self.current_frame[0:10, :], axis=(0,1))
            bottom = np.mean(self.current_frame[h-10:h, :], axis=(0,1))
            left = np.mean(self.current_frame[:, 0:10], axis=(0,1))
            right = np.mean(self.current_frame[:, w-10:w], axis=(0,1))
            
            avg = np.mean([top, bottom, left, right], axis=0)
            r, g, b = int(avg[2]), int(avg[1]), int(avg[0])
            
            self.color_edit.setText(f"{r}, {g}, {b}")
            self.log_message.emit("INFO", f"Background: RGB({r},{g},{b})")
    
    def set_origin(self):
        """Set origin"""
        self.origin_x.setText("150.5")
        self.origin_y.setText("75.2")
        self.log_message.emit("INFO", "Origin set")
    
    def save_vision_data(self):
        """Save all vision data"""
        data = {
            "found_values": {
                "scored_value": self.scored_value.text(),
                "x1_pixel": self.x1_pixel_found.text(),
                "y1_robot": self.y1_robot_found.text(),
                "found_angle": self.found_angle.text(),
                "x2_pixel": self.x2_pixel_found.text(),
                "pixel_x": self.pixel_x_found.text(),
                "y2_pixel": self.y2_pixel_found.text(),
                "robot_x": self.robot_x_found.text(),
                "robot_y": self.robot_y_found.text()
            },
            "calibration_values": {
                "scored_value": self.calib_scored.text(),
                "x1_pixel": self.x1_pixel_calib.text(),
                "y1_robot": self.y1_robot_calib.text(),
                "found_angle": self.calib_angle.text(),
                "x2_pixel": self.x2_pixel_calib.text(),
                "pixel_x": self.pixel_x_calib.text(),
                "y2_pixel": self.y2_pixel_calib.text(),
                "robot_x": self.robot_x_calib.text(),
                "robot_y": self.robot_y_calib.text()
            },
            "settings": {
                "zoom": self.zoom_spin.value(),
                "brightness": self.brightness_slider.value(),
                "contrast": self.contrast_slider.value(),
                "score_threshold": self.score_threshold.value(),
                "background": self.color_edit.text()
            }
        }
        
        filename = f"vision_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        
        self.log_message.emit("INFO", f"Data saved to {filename}")
        QMessageBox.information(self, "Save Vision Data", f"Data saved to {filename}")
    
    def _handle_log(self, level, message):
        """Handle log messages"""
        if hasattr(self.parent, 'add_log'):
            self.parent.add_log(level, f"[Vision] {message}")
    
    def closeEvent(self, event):
        """Clean up on close"""
        self.stop_camera()
        event.accept()