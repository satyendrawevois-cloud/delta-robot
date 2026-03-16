# pick_place_sdk.py
# Professional SDK for Delta Robot

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time

class DeltaSDK:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Delta Robot Pick & Place SDK")
        self.root.geometry("800x600")
        
        # Robot connection
        self.delta = None
        self.connected = False
        
        # Pick positions database
        self.pick_positions = {
            "Object A (Red)": {"x": 100, "y": 50, "z": -200},
            "Object B (Blue)": {"x": 150, "y": -30, "z": -200},
            "Object C (Green)": {"x": 80, "y": -80, "z": -200},
            "Custom": {"x": 0, "y": 0, "z": -200}
        }
        
        # Place positions database
        self.place_positions = {
            "Bin 1 (Left)": {"x": 300, "y": 50, "z": -200},
            "Bin 2 (Right)": {"x": 300, "y": -50, "z": -200},
            "Bin 3 (Center)": {"x": 300, "y": 0, "z": -200},
            "Chute": {"x": 250, "y": 100, "z": -200},
            "Custom": {"x": 0, "y": 0, "z": -200}
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Robot Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0)
        self.port_var = tk.StringVar(value="COM3")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=10).grid(row=0, column=1)
        
        ttk.Button(conn_frame, text="Connect", command=self.connect_robot).grid(row=0, column=2, padx=5)
        ttk.Button(conn_frame, text="Calibrate", command=self.calibrate_robot).grid(row=0, column=3, padx=5)
        ttk.Button(conn_frame, text="Home", command=self.go_home).grid(row=0, column=4, padx=5)
        
        self.conn_status = ttk.Label(conn_frame, text="● Disconnected", foreground="red")
        self.conn_status.grid(row=0, column=5, padx=10)
        
        # Main Program Frame
        prog_frame = ttk.LabelFrame(self.root, text="Pick & Place Program", padding=10)
        prog_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side - Program steps
        left_frame = ttk.Frame(prog_frame)
        left_frame.pack(side="left", fill="both", expand=True)
        
        ttk.Label(left_frame, text="Program Steps:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.steps_listbox = tk.Listbox(left_frame, height=12, width=40)
        self.steps_listbox.pack(fill="both", expand=True, pady=5)
        
        # Buttons for program
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="Add Step", command=self.add_step).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Remove Step", command=self.remove_step).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Move Up", command=self.move_up).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Move Down", command=self.move_down).pack(side="left", padx=2)
        
        # Right side - Configuration
        right_frame = ttk.Frame(prog_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        # Step Configuration
        ttk.Label(right_frame, text="Step Configuration:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        config_frame = ttk.Frame(right_frame)
        config_frame.pack(fill="x", pady=5)
        
        # Step type
        ttk.Label(config_frame, text="Step Type:").grid(row=0, column=0, sticky="w")
        self.step_type = ttk.Combobox(config_frame, values=["Pick", "Place", "Move", "Wait", "Gripper On", "Gripper Off"], width=15)
        self.step_type.grid(row=0, column=1, padx=5)
        self.step_type.set("Pick")
        
        # Object selection
        ttk.Label(config_frame, text="Object:").grid(row=1, column=0, sticky="w")
        self.object_select = ttk.Combobox(config_frame, values=list(self.pick_positions.keys()), width=15)
        self.object_select.grid(row=1, column=1, padx=5)
        self.object_select.set("Object A (Red)")
        
        # Bin selection
        ttk.Label(config_frame, text="Place at:").grid(row=2, column=0, sticky="w")
        self.bin_select = ttk.Combobox(config_frame, values=list(self.place_positions.keys()), width=15)
        self.bin_select.grid(row=2, column=1, padx=5)
        self.bin_select.set("Bin 1 (Left)")
        
        # Speed
        ttk.Label(config_frame, text="Speed (%):").grid(row=3, column=0, sticky="w")
        self.speed_var = tk.IntVar(value=100)
        ttk.Scale(config_frame, from_=10, to=100, variable=self.speed_var, orient="horizontal", length=150).grid(row=3, column=1)
        
        # Custom coordinates
        ttk.Label(config_frame, text="Custom X:").grid(row=4, column=0, sticky="w")
        self.custom_x = ttk.Entry(config_frame, width=10)
        self.custom_x.grid(row=4, column=1, sticky="w")
        self.custom_x.insert(0, "0")
        
        ttk.Label(config_frame, text="Custom Y:").grid(row=5, column=0, sticky="w")
        self.custom_y = ttk.Entry(config_frame, width=10)
        self.custom_y.grid(row=5, column=1, sticky="w")
        self.custom_y.insert(0, "0")
        
        ttk.Label(config_frame, text="Custom Z:").grid(row=6, column=0, sticky="w")
        self.custom_z = ttk.Entry(config_frame, width=10)
        self.custom_z.grid(row=6, column=1, sticky="w")
        self.custom_z.insert(0, "-200")
        
        # Program Control
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(control_frame, text="Generate G-Code", command=self.generate_gcode, width=20).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Run Program", command=self.run_program, width=20).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Save Program", command=self.save_program, width=20).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Load Program", command=self.load_program, width=20).pack(side="left", padx=5)
        
        # Output
        ttk.Label(self.root, text="G-Code Output:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
        self.output_text = tk.Text(self.root, height=10, width=80)
        self.output_text.pack(fill="both", expand=True, padx=10, pady=5)
        
    def add_step(self):
        step_type = self.step_type.get()
        
        if step_type == "Pick":
            obj = self.object_select.get()
            if obj in self.pick_positions:
                pos = self.pick_positions[obj]
                step = f"Pick {obj} at ({pos['x']}, {pos['y']}, {pos['z']})"
            else:
                # Custom position
                x = self.custom_x.get()
                y = self.custom_y.get()
                z = self.custom_z.get()
                step = f"Pick Custom at ({x}, {y}, {z})"
                
        elif step_type == "Place":
            bin_loc = self.bin_select.get()
            if bin_loc in self.place_positions:
                pos = self.place_positions[bin_loc]
                step = f"Place in {bin_loc} at ({pos['x']}, {pos['y']}, {pos['z']})"
            else:
                x = self.custom_x.get()
                y = self.custom_y.get()
                z = self.custom_z.get()
                step = f"Place Custom at ({x}, {y}, {z})"
                
        elif step_type == "Move":
            x = self.custom_x.get()
            y = self.custom_y.get()
            z = self.custom_z.get()
            step = f"Move to ({x}, {y}, {z})"
            
        elif step_type == "Wait":
            step = "Wait 500ms"
            
        elif step_type == "Gripper On":
            step = "Gripper ON"
            
        elif step_type == "Gripper Off":
            step = "Gripper OFF"
            
        self.steps_listbox.insert(tk.END, step)
        
    def remove_step(self):
        selection = self.steps_listbox.curselection()
        if selection:
            self.steps_listbox.delete(selection)
            
    def move_up(self):
        selection = self.steps_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            item = self.steps_listbox.get(idx)
            self.steps_listbox.delete(idx)
            self.steps_listbox.insert(idx-1, item)
            self.steps_listbox.selection_set(idx-1)
            
    def move_down(self):
        selection = self.steps_listbox.curselection()
        if selection and selection[0] < self.steps_listbox.size()-1:
            idx = selection[0]
            item = self.steps_listbox.get(idx)
            self.steps_listbox.delete(idx)
            self.steps_listbox.insert(idx+1, item)
            self.steps_listbox.selection_set(idx+1)
    
    def generate_gcode(self):
        self.output_text.delete(1.0, tk.END)
        
        # Header
        gcode = "; Pick & Place Program Generated by Delta SDK\n"
        gcode += "G90 ; Absolute positioning\n"
        gcode += "G21 ; Units in mm\n"
        gcode += "F2000 ; Default speed\n\n"
        
        line_num = 10
        
        # Convert steps to G-Code
        for i, step in enumerate(self.steps_listbox.get(0, tk.END)):
            if "Pick" in step:
                # Extract coordinates from step string
                # Format: "Pick Object at (x, y, z)"
                import re
                coords = re.findall(r'[-+]?\d*\.?\d+', step)
                if len(coords) >= 3:
                    x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
                    
                    # Approach
                    gcode += f"N{line_num} G00 X{x} Y{y} Z{z+50} F2000 ; Approach\n"
                    line_num += 10
                    
                    # Move down
                    speed = self.speed_var.get()
                    feed = int(500 * speed/100)
                    gcode += f"N{line_num} G01 X{x} Y{y} Z{z} F{feed} ; Move down\n"
                    line_num += 10
                    
                    # Gripper on
                    gcode += f"N{line_num} M03 ; Gripper ON\n"
                    line_num += 10
                    
                    # Wait
                    gcode += f"N{line_num} G04 P500 ; Wait\n"
                    line_num += 10
                    
                    # Lift
                    gcode += f"N{line_num} G00 X{x} Y{y} Z{z-50} F1000 ; Lift\n"
                    line_num += 10
                    
            elif "Place" in step:
                coords = re.findall(r'[-+]?\d*\.?\d+', step)
                if len(coords) >= 3:
                    x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
                    
                    # Approach
                    gcode += f"N{line_num} G00 X{x} Y{y} Z{z+50} F2000 ; Approach bin\n"
                    line_num += 10
                    
                    # Move down
                    speed = self.speed_var.get()
                    feed = int(500 * speed/100)
                    gcode += f"N{line_num} G01 X{x} Y{y} Z{z} F{feed} ; Move down\n"
                    line_num += 10
                    
                    # Gripper off
                    gcode += f"N{line_num} M05 ; Gripper OFF\n"
                    line_num += 10
                    
                    # Wait
                    gcode += f"N{line_num} G04 P500 ; Wait\n"
                    line_num += 10
                    
                    # Lift
                    gcode += f"N{line_num} G00 X{x} Y{y} Z{z-50} F1000 ; Lift\n"
                    line_num += 10
                    
            elif "Move" in step:
                coords = re.findall(r'[-+]?\d*\.?\d+', step)
                if len(coords) >= 3:
                    x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
                    gcode += f"N{line_num} G00 X{x} Y{y} Z{z} F2000 ; Move\n"
                    line_num += 10
                    
            elif "Gripper ON" in step:
                gcode += f"N{line_num} M03 ; Gripper ON\n"
                line_num += 10
                
            elif "Gripper OFF" in step:
                gcode += f"N{line_num} M05 ; Gripper OFF\n"
                line_num += 10
                
            elif "Wait" in step:
                gcode += f"N{line_num} G04 P500 ; Wait\n"
                line_num += 10
        
        # End program
        gcode += f"\nN{line_num} M30 ; End program\n"
        
        self.output_text.insert(1.0, gcode)
        
    def run_program(self):
        if not self.connected:
            messagebox.showerror("Error", "Robot not connected!")
            return
            
        self.generate_gcode()
        gcode = self.output_text.get(1.0, tk.END)
        
        # Send G-Code to robot line by line
        for line in gcode.split('\n'):
            if line and not line.startswith(';'):
                # Extract command (remove comments and line numbers)
                if '(' in line:
                    cmd = line.split('(')[0].strip()
                else:
                    cmd = line.strip()
                    
                if cmd:
                    # Parse G-Code and send to robot
                    self.send_command(cmd)
                    time.sleep(0.1)  # Small delay between commands
        
        messagebox.showinfo("Success", "Program executed!")
        
    def send_command(self, cmd):
        # Convert G-Code to Delta commands
        if cmd.startswith('G00') or cmd.startswith('G01'):
            # Parse X, Y, Z
            import re
            x_match = re.search(r'X([-+]?\d*\.?\d+)', cmd)
            y_match = re.search(r'Y([-+]?\d*\.?\d+)', cmd)
            z_match = re.search(r'Z([-+]?\d*\.?\d+)', cmd)
            
            if x_match and y_match and z_match:
                x = float(x_match.group(1))
                y = float(y_match.group(1))
                z = float(z_match.group(1))
                
                # Send M command to delta
                self.delta.write(f"M X{x} Y{y} Z{z} T1\n".encode())
                resp = self.delta.readline().decode().strip()
                print(f"Response: {resp}")
                
        elif cmd.startswith('M03'):
            self.delta.write(b"GRIP_ON\n")
            self.delta.readline()
            
        elif cmd.startswith('M05'):
            self.delta.write(b"GRIP_OFF\n")
            self.delta.readline()
            
        elif cmd.startswith('G04'):
            # Wait command
            time.sleep(0.5)
    
    def connect_robot(self):
        try:
            self.delta = serial.Serial(self.port_var.get(), 115200, timeout=1)
            time.sleep(2)
            self.connected = True
            self.conn_status.config(text="● Connected", foreground="green")
            messagebox.showinfo("Success", "Robot connected!")
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")
    
    def calibrate_robot(self):
        if not self.connected:
            messagebox.showerror("Error", "Robot not connected!")
            return
            
        self.delta.write(b"CAL\n")
        resp = self.delta.readline().decode().strip()
        if resp == "RDY":
            messagebox.showinfo("Success", "Calibration complete!")
            
    def go_home(self):
        if not self.connected:
            messagebox.showerror("Error", "Robot not connected!")
            return
            
        self.delta.write(b"M X0 Y0 Z-200 T2\n")
        resp = self.delta.readline().decode().strip()
        if resp == "OK":
            print("Home position reached")
    
    def save_program(self):
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(defaultextension=".gcode")
        if filename:
            with open(filename, 'w') as f:
                f.write(self.output_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Program saved to {filename}")
    
    def load_program(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(filetypes=[("G-Code files", "*.gcode")])
        if filename:
            with open(filename, 'r') as f:
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(1.0, f.read())
                
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    sdk = DeltaSDK()
    sdk.run()