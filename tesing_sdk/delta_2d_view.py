#!/usr/bin/env python3
"""
2D View with Image Tracing - Fixed Coordinate System
Run this file directly: python this_file.py
"""

import sys
import math
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ImageTracer2DView(QWidget):
    """2D View with image upload, drag & drop, and tracing capability"""
    
    # Signal for position changes and G-code generation
    position_changed = pyqtSignal(float, float, float)
    gcode_generated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        print("ImageTracer2DView: Initializing...")
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        
        # View parameters
        self.workspace_size = 800  # Actual workspace size in mm
        self.radius = 400  # Circle radius in mm
        self.grid_size = 10  # 10mm grid boxes for accuracy
        
        # Zoom and Pan parameters
        self.zoom_factor = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 5.0
        self.pan_x = 0
        self.pan_y = 0
        self.last_pan_point = None
        self.is_panning = False
        
        # Scroll bars
        self.h_scroll = 0
        self.v_scroll = 0
        self.scroll_step = 50
        
        # World coordinates (mm) - Yehi main coordinates hain
        self.current_x = 0
        self.current_y = 0
        self.current_z = -450  # Default Z
        
        # Hover position in world coordinates (mm)
        self.hover_world_x = None
        self.hover_world_y = None
        self.hover_valid = False
        
        # Drawing related
        self.drawing_mode = False
        self.drawing_points = []  # List of points in world coordinates (mm)
        self.saved_drawings = []  # List of completed drawings in world coordinates
        self.temp_point = None  # Temporary point for preview in world coordinates
        
        # Image related
        self.uploaded_image = None
        self.image_pixmap = None
        self.original_pixmap = None
        self.image_opacity = 1.0
        self.image_scale = 1.0
        self.image_x = 0  # World coordinates (mm)
        self.image_y = 0  # World coordinates (mm)
        self.image_width = 0  # World coordinates (mm)
        self.image_height = 0  # World coordinates (mm)
        self.image_visible = False
        self.image_filename = ""
        self.dragging_image = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.image_locked = False
        self.image_size_mm = 200  # Default image size in mm (circle ke andar fit)
        
        # Arrow angle
        self.arrow_angle = 0
        print("ImageTracer2DView: Initialized")
    
    def set_scroll(self, h, v):
        """Set scroll position"""
        self.h_scroll = h
        self.v_scroll = v
        self.update()
    
    def get_scale(self):
        """Get current scale factor (mm to pixels)"""
        # Widget size ke hisaab se scale calculate karo
        base_scale = min(self.width(), self.height()) / self.workspace_size
        return base_scale * self.zoom_factor
    
    def widget_to_world(self, wx, wy):
        """Convert widget coordinates to world coordinates (mm)"""
        view_center_x = self.width() / 2
        view_center_y = self.height() / 2
        scale = self.get_scale()
        
        # Scroll and pan ko adjust karo
        wx_adj = wx - self.h_scroll
        wy_adj = wy - self.v_scroll
        
        world_x = (wx_adj - view_center_x - self.pan_x) / scale
        world_y = (view_center_y + self.pan_y - wy_adj) / scale
        return world_x, world_y
    
    def world_to_widget(self, wx, wy):
        """Convert world coordinates to widget coordinates (pixels)"""
        view_center_x = self.width() / 2
        view_center_y = self.height() / 2
        scale = self.get_scale()
        
        widget_x = view_center_x + wx * scale + self.pan_x + self.h_scroll
        widget_y = view_center_y - wy * scale + self.pan_y + self.v_scroll
        return widget_x, widget_y
    
    def paintEvent(self, event):
        """Draw the 2D view"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(0, 0, self.width(), self.height(), QColor(240, 240, 240))
        
        # View center in widget coordinates
        view_center_x = self.width() / 2
        view_center_y = self.height() / 2
        
        # Draw fine grid (10mm boxes) - Sab world coordinates ke hisaab se
        self.draw_fine_grid(painter)
        
        # Draw square (800mm workspace) - World coordinates mein
        square_size_world = self.workspace_size
        square_x_world = -square_size_world / 2
        square_y_world = -square_size_world / 2
        
        square_x1, square_y1 = self.world_to_widget(square_x_world, square_y_world)
        square_x2, square_y2 = self.world_to_widget(square_x_world + square_size_world, 
                                                   square_y_world + square_size_world)
        
        painter.setPen(QPen(QColor(100, 100, 255), max(1, int(2 / self.zoom_factor)), Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(int(square_x1), int(square_y1), 
                        int(square_x2 - square_x1), int(square_y2 - square_y1))
        
        # Draw text "800 mm"
        text_x, text_y = self.world_to_widget(square_x_world + 20, square_y_world + 20)
        painter.setPen(QColor(100, 100, 255))
        font = QFont("Arial", max(6, int(9 / self.zoom_factor)))
        painter.setFont(font)
        painter.drawText(int(text_x), int(text_y), "800 mm")
        
        # Draw circle (400mm radius) - World coordinates mein
        circle_x_world = 0
        circle_y_world = 0
        circle_radius_world = self.radius
        
        circle_x, circle_y = self.world_to_widget(circle_x_world, circle_y_world)
        circle_radius_px = circle_radius_world * self.get_scale()
        
        painter.setPen(QPen(QColor(0, 200, 0), max(1, int(3 / self.zoom_factor))))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(circle_x - circle_radius_px), 
                           int(circle_y - circle_radius_px),
                           int(circle_radius_px * 2), 
                           int(circle_radius_px * 2))
        
        # Draw text "R=400 mm"
        text_x, text_y = self.world_to_widget(50, 50)
        painter.setPen(QColor(0, 150, 0))
        painter.drawText(int(text_x), int(text_y), "R=400 mm")
        
        # Draw axes
        painter.setPen(QPen(QColor(150, 150, 150), max(1, int(1 / self.zoom_factor)), Qt.DashLine))
        
        # X-axis
        x1, y1 = self.world_to_widget(-self.workspace_size/2, 0)
        x2, y2 = self.world_to_widget(self.workspace_size/2, 0)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Y-axis
        x1, y1 = self.world_to_widget(0, -self.workspace_size/2)
        x2, y2 = self.world_to_widget(0, self.workspace_size/2)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw center point
        center_x, center_y = self.world_to_widget(0, 0)
        center_size = max(5, int(10 / self.zoom_factor))
        painter.setPen(QPen(QColor(0, 0, 255), max(1, int(3 / self.zoom_factor))))
        painter.setBrush(QBrush(QColor(0, 0, 255)))
        painter.drawEllipse(int(center_x - center_size // 2), 
                           int(center_y - center_size // 2), 
                           center_size, center_size)
        painter.setPen(QColor(0, 0, 150))
        text_x, text_y = self.world_to_widget(10, 10)
        painter.drawText(int(text_x), int(text_y), "Center (0,0)")
        
        # Draw uploaded image if available
        if self.image_visible and self.image_pixmap:
            painter.setOpacity(self.image_opacity)
            
            # Image position in widget coordinates
            img_x, img_y = self.world_to_widget(self.image_x, self.image_y)
            
            # Image size in pixels
            img_width_px = int(self.image_size_mm * self.get_scale())
            img_height_px = int(self.image_size_mm * self.get_scale() * 
                               self.image_height / self.image_width) if self.image_width > 0 else img_width_px
            
            # Scale image
            scaled_pixmap = self.original_pixmap.scaled(
                img_width_px, img_height_px,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Draw image centered at its position
            painter.drawPixmap(int(img_x - scaled_pixmap.width() // 2),
                              int(img_y - scaled_pixmap.height() // 2),
                              scaled_pixmap)
            
            # Draw border if not locked
            if not self.image_locked:
                painter.setOpacity(1.0)
                painter.setPen(QPen(QColor(255, 165, 0), 2, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(int(img_x - scaled_pixmap.width() // 2),
                                int(img_y - scaled_pixmap.height() // 2),
                                scaled_pixmap.width(),
                                scaled_pixmap.height())
            
            painter.setOpacity(1.0)
        
        # Draw all saved drawings
        painter.setPen(QPen(QColor(255, 165, 0), max(1, int(2 / self.zoom_factor))))
        painter.setBrush(Qt.NoBrush)
        for drawing in self.saved_drawings:
            if len(drawing) > 1:
                for i in range(len(drawing) - 1):
                    x1, y1 = self.world_to_widget(drawing[i][0], drawing[i][1])
                    x2, y2 = self.world_to_widget(drawing[i+1][0], drawing[i+1][1])
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw current drawing in progress
        if self.drawing_mode and len(self.drawing_points) > 0:
            painter.setPen(QPen(QColor(255, 0, 0), max(1, int(3 / self.zoom_factor))))
            painter.setBrush(Qt.NoBrush)
            
            # Draw lines between points
            for i in range(len(self.drawing_points) - 1):
                x1, y1 = self.world_to_widget(self.drawing_points[i][0], self.drawing_points[i][1])
                x2, y2 = self.world_to_widget(self.drawing_points[i+1][0], self.drawing_points[i+1][1])
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Draw points
            point_size = max(2, int(5 / self.zoom_factor))
            painter.setPen(QPen(QColor(255, 0, 0), point_size))
            for point in self.drawing_points:
                x, y = self.world_to_widget(point[0], point[1])
                painter.drawPoint(int(x), int(y))
            
            # Draw temporary preview line
            if self.temp_point and len(self.drawing_points) > 0:
                last_point = self.drawing_points[-1]
                x1, y1 = self.world_to_widget(last_point[0], last_point[1])
                x2, y2 = self.temp_point
                
                painter.setPen(QPen(QColor(255, 0, 0, 128), max(1, int(2 / self.zoom_factor)), Qt.DashLine))
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw current position
        if self.current_x != 0 or self.current_y != 0:
            pos_x, pos_y = self.world_to_widget(self.current_x, self.current_y)
            
            # Check if within circle
            distance = math.sqrt(self.current_x**2 + self.current_y**2)
            within_circle = distance <= self.radius
            
            if within_circle:
                dot_size = max(8, int(16 / self.zoom_factor))
                painter.setPen(QPen(QColor(255, 0, 0), max(1, int(3 / self.zoom_factor))))
                painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
                painter.drawEllipse(int(pos_x - dot_size // 2), 
                                   int(pos_y - dot_size // 2), 
                                   dot_size, dot_size)
                
                # Draw arrow
                self.draw_arrow(painter, pos_x, pos_y, self.arrow_angle)
                
                # Position label
                painter.setPen(QColor(200, 0, 0))
                painter.setFont(QFont("Arial", max(6, int(9 / self.zoom_factor)), QFont.Bold))
                text_x, text_y = self.world_to_widget(self.current_x + 15, self.current_y + 15)
                painter.drawText(int(text_x), int(text_y), 
                                f"({self.current_x:.1f}, {self.current_y:.1f})")
        
        # Draw hover position
        if self.hover_world_x is not None and self.hover_world_y is not None and self.hover_valid:
            hover_x, hover_y = self.world_to_widget(self.hover_world_x, self.hover_world_y)
            
            hover_size = max(10, int(20 / self.zoom_factor))
            painter.setPen(QPen(QColor(255, 165, 0), max(1, int(2 / self.zoom_factor)), Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(hover_x - hover_size // 2), 
                               int(hover_y - hover_size // 2), 
                               hover_size, hover_size)
            
            painter.setPen(QColor(255, 140, 0))
            painter.setFont(QFont("Arial", max(6, int(9 / self.zoom_factor)), QFont.Bold))
            text_x, text_y = self.world_to_widget(self.hover_world_x + 15, self.hover_world_y + 15)
            painter.drawText(int(text_x), int(text_y), 
                            f"X: {self.hover_world_x:.1f}, Y: {self.hover_world_y:.1f}")
        
        # Draw image info
        if self.image_visible and self.image_filename:
            painter.resetTransform()
            painter.setPen(QColor(150, 150, 255))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(10, 100, f"Image: {os.path.basename(self.image_filename)}")
            painter.drawText(10, 120, f"Opacity: {int(self.image_opacity * 100)}%")
            painter.drawText(10, 140, f"Position: X={self.image_x:.1f}, Y={self.image_y:.1f}")
            painter.drawText(10, 160, f"Size: {self.image_size_mm:.0f}mm")
            if self.image_locked:
                painter.drawText(10, 180, "Status: LOCKED")
            else:
                painter.drawText(10, 180, "Status: Move with mouse")
        
        # Draw zoom level indicator
        painter.resetTransform()
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, 30, f"Zoom: {self.zoom_factor:.1f}x")
        
        # Draw mode indicator
        if self.drawing_mode:
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(10, 50, "Mode: DRAWING")
        else:
            painter.setPen(QColor(0, 0, 255))
            painter.drawText(10, 50, "Mode: SELECT")
        
        # Draw instructions
        painter.setPen(QColor(100, 100, 100))
        painter.drawText(10, 70, "Mouse Wheel: Zoom | Right Drag: Pan | Scroll Bars: Move")
    
    def draw_fine_grid(self, painter):
        """Draw fine grid with 10mm boxes in world coordinates"""
        painter.setPen(QPen(QColor(200, 200, 200), max(1, int(1 / self.zoom_factor)), Qt.SolidLine))
        
        # Grid spacing in mm
        grid_spacing_mm = self.grid_size
        
        # Grid range in mm
        grid_min = -self.workspace_size // 2
        grid_max = self.workspace_size // 2
        
        # Draw vertical grid lines
        for x in range(grid_min, grid_max + 1, grid_spacing_mm):
            x1, y1 = self.world_to_widget(x, grid_min)
            x2, y2 = self.world_to_widget(x, grid_max)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw horizontal grid lines
        for y in range(grid_min, grid_max + 1, grid_spacing_mm):
            x1, y1 = self.world_to_widget(grid_min, y)
            x2, y2 = self.world_to_widget(grid_max, y)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw thicker lines every 50mm
        painter.setPen(QPen(QColor(150, 150, 150), max(1, int(2 / self.zoom_factor))))
        for x in range(grid_min, grid_max + 1, 50):
            if x % 50 == 0:
                x1, y1 = self.world_to_widget(x, grid_min)
                x2, y2 = self.world_to_widget(x, grid_max)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        for y in range(grid_min, grid_max + 1, 50):
            if y % 50 == 0:
                x1, y1 = self.world_to_widget(grid_min, y)
                x2, y2 = self.world_to_widget(grid_max, y)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def draw_arrow(self, painter, x, y, angle):
        """Draw arrow at position"""
        arrow_length = int(30 / self.zoom_factor)
        arrow_size = int(10 / self.zoom_factor)
        
        end_x = int(x + arrow_length * math.cos(math.radians(angle)))
        end_y = int(y - arrow_length * math.sin(math.radians(angle)))
        
        # Draw arrow line
        painter.setPen(QPen(QColor(255, 0, 0), max(1, int(2 / self.zoom_factor))))
        painter.drawLine(int(x), int(y), end_x, end_y)
        
        # Draw arrow head
        head_angle1 = angle + 150
        head_angle2 = angle - 150
        
        head_x1 = int(end_x + arrow_size * math.cos(math.radians(head_angle1)))
        head_y1 = int(end_y - arrow_size * math.sin(math.radians(head_angle1)))
        head_x2 = int(end_x + arrow_size * math.cos(math.radians(head_angle2)))
        head_y2 = int(end_y - arrow_size * math.sin(math.radians(head_angle2)))
        
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawPolygon(
            QPoint(end_x, end_y),
            QPoint(head_x1, head_y1),
            QPoint(head_x2, head_y2)
        )
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        # Get mouse position in world coordinates
        world_x, world_y = self.widget_to_world(event.x(), event.y())
        
        # Calculate zoom factor change
        zoom_factor = 1.1
        if event.angleDelta().y() > 0:
            # Zoom in
            new_zoom = self.zoom_factor * zoom_factor
        else:
            # Zoom out
            new_zoom = self.zoom_factor / zoom_factor
        
        # Apply zoom limits
        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return
        
        # Update zoom
        self.zoom_factor = new_zoom
        
        # After zoom, pan to keep world point under mouse
        new_widget_x, new_widget_y = self.world_to_widget(world_x, world_y)
        self.pan_x += (new_widget_x - event.x())
        self.pan_y += (new_widget_y - event.y())
        
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning, drawing, or image drag"""
        if event.button() == Qt.RightButton:
            # Start panning
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        
        elif event.button() == Qt.LeftButton:
            if not self.is_panning:
                # Get world coordinates
                world_x, world_y = self.widget_to_world(event.x(), event.y())
                
                # Check if clicking on image for drag
                if self.image_visible and self.image_pixmap and not self.image_locked:
                    # Check distance from image center
                    distance = math.sqrt((world_x - self.image_x)**2 + (world_y - self.image_y)**2)
                    if distance < self.image_size_mm / 2:
                        # Start dragging image
                        self.dragging_image = True
                        self.drag_start_x = event.x()
                        self.drag_start_y = event.y()
                        self.setCursor(Qt.DragMoveCursor)
                        return
                
                # Check if within circle
                distance = math.sqrt(world_x**2 + world_y**2)
                if distance <= self.radius:
                    if self.drawing_mode:
                        # Add point to current drawing
                        self.drawing_points.append((world_x, world_y))
                        self.temp_point = None
                        self.update()
                    else:
                        # Normal mode - set position and generate G-code
                        self.current_x = world_x
                        self.current_y = world_y
                        if world_x != 0 or world_y != 0:
                            self.arrow_angle = math.degrees(math.atan2(world_y, world_x))
                        
                        # Emit position signal
                        self.position_changed.emit(self.current_x, self.current_y, self.current_z)
                        
                        # Generate and emit G-code
                        gcode = self.generate_gcode(world_x, world_y, self.current_z)
                        self.gcode_generated.emit(gcode)
                        
                        self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for hover, panning, drawing preview, and image drag"""
        if self.is_panning and self.last_pan_point:
            # Pan the view
            delta = event.pos() - self.last_pan_point
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_pan_point = event.pos()
            self.update()
        
        elif self.dragging_image:
            # Drag image in world coordinates
            world_x, world_y = self.widget_to_world(event.x(), event.y())
            self.image_x = world_x
            self.image_y = world_y
            self.update()
        
        else:
            # Update hover position in world coordinates
            world_x, world_y = self.widget_to_world(event.x(), event.y())
            distance = math.sqrt(world_x**2 + world_y**2)
            self.hover_valid = distance <= self.radius
            
            if self.hover_valid:
                self.hover_world_x = world_x
                self.hover_world_y = world_y
            else:
                self.hover_world_x = None
                self.hover_world_y = None
            
            # Update temporary point for drawing preview
            if self.drawing_mode and len(self.drawing_points) > 0 and self.hover_valid:
                self.temp_point = (event.x(), event.y())
            else:
                self.temp_point = None
            
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.RightButton:
            self.is_panning = False
            self.last_pan_point = None
            self.setCursor(Qt.ArrowCursor)
        
        elif event.button() == Qt.LeftButton and self.dragging_image:
            self.dragging_image = False
            self.setCursor(Qt.ArrowCursor)
    
    def dragEnterEvent(self, event):
        """Handle drag enter for image files"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    event.acceptProposedAction()
                    return
    
    def dropEvent(self, event):
        """Handle drop event for image files"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.load_image(file_path)
                event.acceptProposedAction()
                break
    
    def generate_gcode(self, x, y, z):
        """Generate G-code from clicked position"""
        gcode = f"G01 X{x:.1f} Y{y:.1f} Z{z:.1f} F1000"
        return gcode
    
    def leaveEvent(self, event):
        """Clear hover when mouse leaves"""
        self.hover_world_x = None
        self.hover_world_y = None
        self.hover_valid = False
        self.temp_point = None
        self.update()
    
    def update_position(self, x, y, z=None):
        """Update current position"""
        self.current_x = x
        self.current_y = y
        if z is not None:
            self.current_z = z
        self.update()
    
    def set_z(self, z):
        """Set Z value"""
        self.current_z = z
        self.update()
    
    def start_drawing(self):
        """Start drawing mode"""
        self.drawing_mode = True
        self.drawing_points = []
        self.update()
    
    def stop_drawing(self):
        """Stop drawing mode and save drawing"""
        if len(self.drawing_points) > 1:
            self.saved_drawings.append(self.drawing_points.copy())
        self.drawing_mode = False
        self.drawing_points = []
        self.temp_point = None
        self.update()
    
    def clear_drawings(self):
        """Clear all drawings"""
        self.saved_drawings = []
        self.drawing_points = []
        self.drawing_mode = False
        self.temp_point = None
        self.update()
    
    def generate_drawing_gcode(self):
        """Generate G-code for the current drawing"""
        if len(self.drawing_points) < 2 and len(self.saved_drawings) == 0:
            return None
        
        gcode_lines = []
        gcode_lines.append(f"; Drawing G-code - Z={self.current_z:.1f}mm")
        gcode_lines.append("G21 ; Set units to mm")
        gcode_lines.append("G90 ; Absolute positioning")
        gcode_lines.append("")
        
        # Add all saved drawings
        for idx, drawing in enumerate(self.saved_drawings):
            if len(drawing) >= 2:
                gcode_lines.append(f"; Drawing {idx+1}")
                for i, point in enumerate(drawing):
                    if i == 0:
                        gcode_lines.append(f"G00 X{point[0]:.1f} Y{point[1]:.1f} Z{self.current_z:.1f} F2000")
                    else:
                        gcode_lines.append(f"G01 X{point[0]:.1f} Y{point[1]:.1f} Z{self.current_z:.1f} F1000")
                gcode_lines.append("")
        
        # Add current drawing if any
        if len(self.drawing_points) >= 2:
            gcode_lines.append("; Current Drawing")
            for i, point in enumerate(self.drawing_points):
                if i == 0:
                    gcode_lines.append(f"G00 X{point[0]:.1f} Y{point[1]:.1f} Z{self.current_z:.1f} F2000")
                else:
                    gcode_lines.append(f"G01 X{point[0]:.1f} Y{point[1]:.1f} Z{self.current_z:.1f} F1000")
        
        return "\n".join(gcode_lines)
    
    def resizeEvent(self, event):
        """Handle resize to maintain aspect ratio"""
        super().resizeEvent(event)
        self.update()
    
    def reset_view(self):
        """Reset zoom and pan to default"""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.h_scroll = 0
        self.v_scroll = 0
        self.update()
    
    def load_image(self, filename):
        """Load image for tracing"""
        try:
            self.original_pixmap = QPixmap(filename)
            if not self.original_pixmap.isNull():
                self.image_pixmap = self.original_pixmap
                self.image_filename = filename
                self.image_visible = True
                self.image_x = 0
                self.image_y = 0
                self.image_locked = False
                self.image_width = self.original_pixmap.width()
                self.image_height = self.original_pixmap.height()
                self.image_size_mm = 200  # Default size
                self.update()
                return True
            else:
                return False
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def set_image_opacity(self, opacity):
        """Set image opacity (0.0 to 1.0)"""
        self.image_opacity = max(0.1, min(1.0, opacity))
        self.update()
    
    def toggle_image_visibility(self, visible):
        """Toggle image visibility"""
        self.image_visible = visible
        self.update()
    
    def center_image(self):
        """Center image in workspace"""
        self.image_x = 0
        self.image_y = 0
        self.update()
    
    def lock_image(self, locked):
        """Lock/unlock image position"""
        self.image_locked = locked
        self.update()
    
    def increase_image_size(self):
        """Increase image size"""
        self.image_size_mm = min(400, self.image_size_mm + 10)
        self.update()
    
    def decrease_image_size(self):
        """Decrease image size"""
        self.image_size_mm = max(50, self.image_size_mm - 10)
        self.update()


class MainWindow(QMainWindow):
    """Main window with 2D view, drawing tools, and image tracing"""
    
    def __init__(self):
        super().__init__()
        print("MainWindow: Initializing...")
        self.setWindowTitle("2D View with Image Tracing - Fixed Coordinates")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Top panel - Title
        title = QLabel("2D VIEW WITH IMAGE TRACING - Click anywhere inside circle")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background-color: #e0e0e0; border-radius: 5px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Middle panel - 2D View with scroll bars
        view_container = QWidget()
        view_layout = QVBoxLayout(view_container)
        view_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2D View widget
        self.view = ImageTracer2DView()
        
        # Scroll bars
        self.h_scroll = QScrollBar(Qt.Horizontal)
        self.v_scroll = QScrollBar(Qt.Vertical)
        
        # Configure scroll bars
        self.h_scroll.setRange(-1000, 1000)
        self.v_scroll.setRange(-1000, 1000)
        self.h_scroll.setValue(0)
        self.v_scroll.setValue(0)
        self.h_scroll.setPageStep(100)
        self.v_scroll.setPageStep(100)
        
        # Connect scroll bars
        self.h_scroll.valueChanged.connect(self.on_h_scroll)
        self.v_scroll.valueChanged.connect(self.on_v_scroll)
        
        # Layout with scroll bars
        scroll_layout = QGridLayout()
        scroll_layout.addWidget(self.view, 0, 0)
        scroll_layout.addWidget(self.v_scroll, 0, 1)
        scroll_layout.addWidget(self.h_scroll, 1, 0)
        view_layout.addLayout(scroll_layout)
        
        main_layout.addWidget(view_container, 3)
        
        # Bottom panel - Controls
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        
        # Left controls - Drawing tools
        drawing_group = QGroupBox("Drawing Tools")
        drawing_layout = QVBoxLayout(drawing_group)
        
        # Position display
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        self.x_label = QLabel("0.0")
        self.x_label.setStyleSheet("font-weight: bold; color: #1976d2; min-width: 60px;")
        pos_layout.addWidget(self.x_label)
        
        pos_layout.addWidget(QLabel("Y:"))
        self.y_label = QLabel("0.0")
        self.y_label.setStyleSheet("font-weight: bold; color: #1976d2; min-width: 60px;")
        pos_layout.addWidget(self.y_label)
        
        pos_layout.addWidget(QLabel("Z:"))
        self.z_label = QLabel("-450.0")
        self.z_label.setStyleSheet("font-weight: bold; color: #1976d2; min-width: 60px;")
        pos_layout.addWidget(self.z_label)
        
        drawing_layout.addLayout(pos_layout)
        
        # Drawing buttons
        btn_layout1 = QHBoxLayout()
        
        self.draw_btn = QPushButton("✏️ Start Drawing")
        self.draw_btn.clicked.connect(self.start_drawing)
        btn_layout1.addWidget(self.draw_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop Drawing")
        self.stop_btn.clicked.connect(self.stop_drawing)
        self.stop_btn.setEnabled(False)
        btn_layout1.addWidget(self.stop_btn)
        
        drawing_layout.addLayout(btn_layout1)
        
        btn_layout2 = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.clicked.connect(self.clear_drawings)
        btn_layout2.addWidget(self.clear_btn)
        
        self.generate_btn = QPushButton("🎯 Generate G-code")
        self.generate_btn.clicked.connect(self.generate_drawing_gcode)
        btn_layout2.addWidget(self.generate_btn)
        
        drawing_layout.addLayout(btn_layout2)
        
        bottom_layout.addWidget(drawing_group)
        
        # Middle controls - Image tools
        image_group = QGroupBox("Image Tracing")
        image_layout = QVBoxLayout(image_group)
        
        # Image upload button
        upload_btn = QPushButton("📁 Upload Image")
        upload_btn.clicked.connect(self.upload_image)
        image_layout.addWidget(upload_btn)
        
        # Image controls
        img_control_layout = QHBoxLayout()
        
        self.image_visible_check = QCheckBox("Show Image")
        self.image_visible_check.setChecked(True)
        self.image_visible_check.toggled.connect(self.toggle_image)
        img_control_layout.addWidget(self.image_visible_check)
        
        self.center_img_btn = QPushButton("Center")
        self.center_img_btn.clicked.connect(self.center_image)
        img_control_layout.addWidget(self.center_img_btn)
        
        image_layout.addLayout(img_control_layout)
        
        # Image size controls
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 800)
        self.size_slider.setValue(200)
        self.size_slider.valueChanged.connect(self.change_image_size)
        size_layout.addWidget(self.size_slider)
        
        self.size_label = QLabel("200mm")
        self.size_label.setMinimumWidth(50)
        size_layout.addWidget(self.size_label)
        
        image_layout.addLayout(size_layout)
        
        # Lock image button
        lock_layout = QHBoxLayout()
        self.lock_image_check = QCheckBox("Lock Image Position")
        self.lock_image_check.toggled.connect(self.lock_image)
        lock_layout.addWidget(self.lock_image_check)
        image_layout.addLayout(lock_layout)
        
        # Opacity slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        self.opacity_label.setMinimumWidth(40)
        opacity_layout.addWidget(self.opacity_label)
        
        image_layout.addLayout(opacity_layout)
        
        # Drag & Drop hint
        drag_hint = QLabel("💡 Drag & Drop images directly onto canvas")
        drag_hint.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        image_layout.addWidget(drag_hint)
        
        bottom_layout.addWidget(image_group)
        
        # Right controls - Z Control
        z_group = QGroupBox("Z-AXIS CONTROL")
        z_layout = QVBoxLayout(z_group)
        
        # Z Slider
        z_layout.addWidget(QLabel("Z Position:"))
        
        self.z_slider = QSlider(Qt.Horizontal)
        self.z_slider.setRange(-600, -300)
        self.z_slider.setValue(-450)
        self.z_slider.setTickPosition(QSlider.TicksBelow)
        self.z_slider.setTickInterval(10)
        self.z_slider.valueChanged.connect(self.on_z_changed)
        z_layout.addWidget(self.z_slider)
        
        # Z value display
        z_value_layout = QHBoxLayout()
        z_value_layout.addWidget(QLabel("Value:"))
        self.z_value_label = QLabel("-450 mm")
        self.z_value_label.setStyleSheet("font-weight: bold; color: #4caf50;")
        z_value_layout.addWidget(self.z_value_label)
        z_value_layout.addStretch()
        z_layout.addLayout(z_value_layout)
        
        # Z range
        z_range = QLabel("Range: -300 to -600 mm (10mm steps)")
        z_range.setStyleSheet("color: #666; font-size: 10px;")
        z_layout.addWidget(z_range)
        
        bottom_layout.addWidget(z_group)
        
        # FNC label
        fnc_label = QLabel("FNC")
        fnc_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #9c27b0; padding: 10px;")
        bottom_layout.addWidget(fnc_label)
        
        main_layout.addWidget(bottom_panel)
        
        # G-code display at bottom
        gcode_frame = QGroupBox("Generated G-code")
        gcode_frame.setStyleSheet("QGroupBox { font-weight: bold; }")
        gcode_layout = QVBoxLayout(gcode_frame)
        
        self.gcode_display = QTextEdit()
        self.gcode_display.setMaximumHeight(100)
        self.gcode_display.setReadOnly(True)
        self.gcode_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New';
                font-size: 12px;
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        gcode_layout.addWidget(self.gcode_display)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy G-code")
        copy_btn.clicked.connect(self.copy_gcode)
        gcode_layout.addWidget(copy_btn)
        
        main_layout.addWidget(gcode_frame)
        
        # Connect signals
        self.view.position_changed.connect(self.on_position_changed)
        self.view.gcode_generated.connect(self.on_gcode_generated)
        
        # Initial update
        self.on_position_changed(0, 0, -450)
        print("MainWindow: Initialized")
    
    def on_h_scroll(self, value):
        """Handle horizontal scroll"""
        self.view.set_scroll(value, self.v_scroll.value())
    
    def on_v_scroll(self, value):
        """Handle vertical scroll"""
        self.view.set_scroll(self.h_scroll.value(), value)
    
    def on_position_changed(self, x, y, z):
        """Handle position change from 2D view"""
        self.x_label.setText(f"{x:.1f}")
        self.y_label.setText(f"{y:.1f}")
        self.z_label.setText(f"{z:.1f}")
    
    def on_z_changed(self, value):
        """Handle Z slider change"""
        self.z_value_label.setText(f"{value} mm")
        self.view.set_z(value)
        self.z_label.setText(f"{value:.1f}")
    
    def on_gcode_generated(self, gcode):
        """Handle G-code generation"""
        current_text = self.gcode_display.toPlainText()
        if current_text:
            self.gcode_display.setText(gcode + "\n" + current_text)
        else:
            self.gcode_display.setText(gcode)
        
        self.gcode_display.moveCursor(QTextCursor.Start)
    
    def start_drawing(self):
        """Start drawing mode"""
        self.view.start_drawing()
        self.draw_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop_drawing(self):
        """Stop drawing mode"""
        self.view.stop_drawing()
        self.draw_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def clear_drawings(self):
        """Clear all drawings"""
        reply = QMessageBox.question(self, "Clear Drawings", 
                                    "Are you sure you want to clear all drawings?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.view.clear_drawings()
            self.draw_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def generate_drawing_gcode(self):
        """Generate G-code for all drawings"""
        gcode = self.view.generate_drawing_gcode()
        if gcode:
            self.gcode_display.setText(gcode)
            QMessageBox.information(self, "Success", "Drawing G-code generated!")
        else:
            QMessageBox.warning(self, "No Drawing", "No drawings to generate G-code!")
    
    def copy_gcode(self):
        """Copy G-code to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.gcode_display.toPlainText())
        QMessageBox.information(self, "Copied", "G-code copied to clipboard!")
    
    def upload_image(self):
        """Upload image for tracing"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        if file_path:
            if self.view.load_image(file_path):
                QMessageBox.information(self, "Success", f"Image loaded: {os.path.basename(file_path)}")
                self.image_visible_check.setChecked(True)
                self.lock_image_check.setChecked(False)
                self.size_slider.setValue(200)
            else:
                QMessageBox.warning(self, "Error", "Failed to load image!")
    
    def toggle_image(self, checked):
        """Toggle image visibility"""
        self.view.toggle_image_visibility(checked)
    
    def change_opacity(self, value):
        """Change image opacity"""
        opacity = value / 100.0
        self.view.set_image_opacity(opacity)
        self.opacity_label.setText(f"{value}%")
    
    def center_image(self):
        """Center image in workspace"""
        self.view.center_image()
    
    def lock_image(self, checked):
        """Lock/unlock image position"""
        self.view.lock_image(checked)
    
    def change_image_size(self, value):
        """Change image size"""
        # Update view's image size
        self.view.image_size_mm = value
        self.size_label.setText(f"{value}mm")
        self.view.update()


if __name__ == "__main__":
    print("=" * 50)
    print("Starting 2D View with Image Tracing Application...")
    print("=" * 50)
    
    # Create QApplication
    app = QApplication(sys.argv)
    print("QApplication created")
    
    # Set application style
    app.setStyle('Fusion')
    print("Application style set")
    
    # Create and show main window
    print("Creating MainWindow...")
    window = MainWindow()
    print("Showing MainWindow...")
    window.show()
    
    print("=" * 50)
    print("Application is running. Close window to exit.")
    print("=" * 50)
    
    # Start event loop
    sys.exit(app.exec_())