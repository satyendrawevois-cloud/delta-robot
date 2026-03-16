import json
import os
import re
from datetime import datetime

def load_config(config_file="comm_config.json"):
    """Load configuration from file"""
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                return json.load(f)
    except:
        pass
    return {"port": "", "baudrate": 9600}

def save_config(config, config_file="comm_config.json"):
    """Save configuration to file"""
    try:
        with open(config_file, "w") as f:
            json.dump(config, f)
        return True
    except:
        return False

def extract_value(command, letter):
    """Extract value after letter in command"""
    pattern = f'{letter}([+-]?\\d+\\.?\\d*)'
    match = re.search(pattern, command)
    if match:
        return match.group(1)
    return None

def parse_goto_command(command):
    """Parse GOTO command from string"""
    parts = command.split()
    if len(parts) >= 5 and parts[0] == "GOTO":
        try:
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])
            time_val = float(parts[4])
            return x, y, z, time_val
        except:
            pass
    return None

def format_goto_command(x, y, z, time_val):
    """Format GOTO command"""
    return f"GOTO {x} {y} {z} {time_val}"

def get_timestamp():
    """Get current timestamp"""
    return datetime.now().strftime("%H:%M:%S")

# ===== NEW FUNCTIONS FOR G-CODE BUFFER MODE =====

def format_gcode_buffer(points):
    """Format list of points as GCODE_BUFFER command for Arduino planner
    
    Args:
        points: List of tuples (x, y, z)
    
    Returns:
        String: "GCODE_BUFFER x1,y1,z1;x2,y2,z2;..."
    """
    points_str = ";".join([f"{x},{y},{z}" for x, y, z in points])
    return f"GCODE_BUFFER {points_str}"

def parse_gcode_buffer(command):
    """Parse GCODE_BUFFER command back to list of points
    
    Args:
        command: String starting with "GCODE_BUFFER"
    
    Returns:
        List of tuples [(x1,y1,z1), (x2,y2,z2), ...] or None
    """
    if command.startswith("GCODE_BUFFER"):
        points_str = command[13:].strip()  # Remove "GCODE_BUFFER "
        points = []
        for point_str in points_str.split(';'):
            try:
                x, y, z = map(float, point_str.split(','))
                points.append((x, y, z))
            except ValueError:
                # Skip invalid points
                continue
        return points
    return None

def count_points_in_buffer(command):
    """Count number of points in a GCODE_BUFFER command"""
    if command.startswith("GCODE_BUFFER"):
        return command.count(';') + 1
    return 0