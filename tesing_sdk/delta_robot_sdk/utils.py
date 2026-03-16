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