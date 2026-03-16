import serial
import serial.tools.list_ports
import threading
import time
from PyQt5.QtCore import QThread, pyqtSignal

class SerialThread(QThread):
    """Thread for serial communication"""
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.is_running = False
        self.port = ""
        self.baudrate = 115200
        
    def connect(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.is_running = True
        self.start()
        
    def disconnect(self):
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.wait()
        
    def send_command(self, command):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(f"{command}\r\n".encode())
                return True
            except Exception as e:
                self.error_occurred.emit(f"Send error: {str(e)}")
                return False
        return False
        
    def run(self):
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            
            self.connection_status.emit(True, f"Connected to {self.port}")
            
            while self.is_running and self.serial_port and self.serial_port.is_open:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode().strip()
                    if data:
                        self.data_received.emit(data)
                time.sleep(0.01)
                
        except Exception as e:
            self.connection_status.emit(False, f"Connection failed: {str(e)}")
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

def get_available_ports():
    """Get list of available serial ports"""
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append({
            'device': port.device,
            'description': port.description,
            'display': f"{port.device} - {port.description}"
        })
    return ports