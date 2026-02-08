from PIL import Image, ImageTk  # add at top with other imports
import tkinter as tk
import time
import math


class CanSatGUI:
    def __init__(self, root):
        root.title("What Our CanSat Sees and Feels")
        root.configure(bg="black")

        # --- Add margins ---
        root.grid_columnconfigure(0, weight=1, minsize=25)   # left margin (extra space)
        root.grid_columnconfigure(9, weight=1, minsize=60)   # right margin (extra space)
        root.grid_rowconfigure(7, minsize=50)  # bottom margin row
        root.grid_rowconfigure(8, minsize=15)  


        # -----------------------------
        # Top Frame for Logo + Title + Right Logo
        # -----------------------------
        top_frame = tk.Frame(root, bg="black")
        top_frame.grid(row=0, column=0, columnspan=999, pady=(20,20), sticky="ew")  # span full width
        root.grid_columnconfigure(0, weight=1)   # make sure frame stretches

        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=2)  # middle gets more space
        top_frame.grid_columnconfigure(2, weight=1)

        # Left Logo
        logo_left_img = Image.open("logo.png").resize((110, 100))
        logo_left = ImageTk.PhotoImage(logo_left_img)
        logo_left_label = tk.Label(top_frame, image=logo_left, bg="black")
        logo_left_label.image = logo_left
        logo_left_label.grid(row=0, column=0, sticky="w", padx=(40,10))

        # Title (centered)
        top_frame.grid_rowconfigure(0, weight=1)

        # Title (vertically and horizontally centered in column 1)
        title = tk.Label(
            top_frame, text="Raw Data from CanSat Sensors",
            font=("Arial", 22, "bold"), fg="gold", bg="black"
        )
        title.grid(row=0, column=1, sticky="nsew", padx=10)

        # Right Logo
        logo_right_img = Image.open("logo2.png").resize((110, 100))   # <-- second logo file
        logo_right = ImageTk.PhotoImage(logo_right_img)
        logo_right_label = tk.Label(top_frame, image=logo_right, bg="black")
        logo_right_label.image = logo_right
        logo_right_label.grid(row=0, column=2, sticky="e", padx=(10,40))


        # -----------------------------
        # Bottom-Right Logo (lower right corner, row 7 area)
        # -----------------------------
        # -----------------------------
        # Bottom-Right Logo (overlay in free space)
        # -----------------------------
        bottom_right_img = Image.open("logo3.png").resize((100, 90))
        bottom_right = ImageTk.PhotoImage(bottom_right_img)

        bottom_right_label = tk.Label(root, image=bottom_right, bg="black")
        bottom_right_label.image = bottom_right

        # Place it in the lower-right corner (relative to window size)
        bottom_right_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-00)

        # -----------------------------
        # Variables
        # -----------------------------
        self.vars = {name: tk.StringVar(value="0") for name in [
            "ax","ay","az", "gx","gy","gz", "mx","my","mz",
            "temp","press","alt","head", "sat","lat","lon","gpsAlt","HardwareTimestamp"
        ]}
        self.last_timestamps = []   # holds recent timestamps
        self.last_update = 1.0
        self.update_rate = 25
        self.update_rate_var = tk.StringVar(value="0")
        self.magnetic_field = 0.1
        self.magnetic_field_var = tk.StringVar(value="0")

        # Bias Corrections for Magnetic field
        self.bias = { name: 0.0 for name in ["ax","ay","az", "mx","my","mz"] }
        
        # MAgnetometer Biases
        self.bias['mx'] = 0.0
        self.bias['my'] = 0.0
        self.bias['mz'] = 0.0
        # Accelerometer Biases
        self.bias['ax'] = 0.0
        self.bias['ay'] = 0.0
        self.bias['az'] = 0.0        


        self.gui_time = 0.0
        self.powerup_time = 1000* time.time()   #ms
        self.python_time_var = tk.StringVar(value="0")
        self.hwTimeOffset = 0.0
        


        # -----------------------------
        # Helpers
        # -----------------------------
        def section_label(text, r):
            lbl = tk.Label(root, text=text, font=("Arial", 18, "bold"),
                           fg="gold", bg="black", anchor="w")
            lbl.grid(row=r, column=1, sticky="w", padx=(30, 5), pady=(5,5))

        def field(parent_row, parent_col, label_text, var, width=8, fontsize=16):
            col = parent_col + 1
            lbl = tk.Label(root, text=label_text, font=("Arial", fontsize, "bold"),
                           fg="gold", bg="black", anchor="e", width=6)
            lbl.grid(row=parent_row, column=col,
                     padx=(8, 4), pady=(5,5), sticky="e")

            ent = tk.Entry(root, textvariable=var, width=width,
                           font=("Arial", fontsize, "bold"),
                           fg="gold", bg="black", justify="right")
            ent.grid(row=parent_row, column=col+1,
                     padx=(4, 30), pady=(5,5), sticky="w")
            return ent



        # -----------------------------
        # Accelerometer Row
        # -----------------------------
        section_label("Accelerometer (m/s²)", 1)
        field(1, 1, "ax", self.vars["ax"])
        field(1, 3, "ay", self.vars["ay"])
        field(1, 5, "az", self.vars["az"])

        # -----------------------------
        # Gyroscope Row
        # -----------------------------
        section_label("Gyroscope (rad/s)", 2)
        field(2, 1, "gx", self.vars["gx"])
        field(2, 3, "gy", self.vars["gy"])
        field(2, 5, "gz", self.vars["gz"])

        # -----------------------------
        # Magnetometer Row
        # -----------------------------
        section_label("Magnetometer (µT)", 3)
        field(3, 1, "mx", self.vars["mx"])
        field(3, 3, "my", self.vars["my"])
        field(3, 5, "mz", self.vars["mz"])
        field(3, 7, "mag", self.magnetic_field_var)

        # -----------------------------
        # Environment Row
        # -----------------------------
        section_label("Environment", 4)
        field(4, 1, "T (°C)", self.vars["temp"])
        field(4, 3, "P (Pa)", self.vars["press"])
        field(4, 5, "Alt (m)", self.vars["alt"])
        field(4, 7, "Head", self.vars["head"])

        # -----------------------------
        # GPS Row
        # -----------------------------
        section_label("GPS", 5)
        field(5, 1, "Sat", self.vars["sat"])
        field(5, 3, "Lat", self.vars["lat"])
        field(5, 5, "Lon", self.vars["lon"])
        field(5, 7, "GPSAlt", self.vars["gpsAlt"])

        # -----------------------------
        # Update Rate Row
        # -----------------------------
        section_label("Update Rate (Hz)", 6)
        field(6, 1, "", self.update_rate_var)

                # -----------------------------
        # Update Rate Row
        # -----------------------------
        section_label("Timestamp (ms)", 7)
        field(7, 1, "HW", self.vars["HardwareTimestamp"])
        field(7, 3, "SW", self.python_time_var)


    def update_state(self, data):
            # --- Update rate calculation ---
        now = float(data['HardwareTimestamp'])/1000
        interval = now - self.last_update
        self.last_update = now
        if interval > 0:  # avoid div by zero
            self.last_timestamps.append(interval)
            if len(self.last_timestamps) > 10:
                self.last_timestamps.pop(0)

            avg_interval = sum(self.last_timestamps) / len(self.last_timestamps)
            update_rate = 1.0 / avg_interval if avg_interval > 0 else 0.0
            self.update_rate = update_rate

            # Bias Corrections 
        data['ax'] = data['ax'] - self.bias['ax']
        data['ay'] = data['ay'] - self.bias['ay']
        data['az'] = data['az'] - self.bias['az']

        data['mx'] = data['mx'] - self.bias['mx']
        data['my'] = data['my'] - self.bias['my']
        data['mz'] = data['mz'] - self.bias['mz']


        # Magnetic Field Calculations
        mx = float(data['mx'])
        my = float(data['my'])
        mz = float(data['mz'])
        self.magnetic_field = math.sqrt ( mx * mx + my * my + mz * mz ) 



    def update_fields(self, data):
        """
        Update GUI fields with new sensor data.
        `data` should be a dict with keys matching self.vars
        """
        for key, value in data.items():
            if key in self.vars and key != "UpdateRate":
                # Format numbers nicely
                if isinstance(value, float):
                    self.vars[key].set(f"{value:.2f}")
                else:
                    self.vars[key].set(str(value))
 
        self.update_rate_var.set(f"{self.update_rate:.2f}")   # convert to string for tkinter
        self.magnetic_field_var.set(f"{self.magnetic_field:.2f}")      
        self.python_time_var.set(f"{self.getPythonTimestamp(data) :.0f}")
        

    def getPythonTimestamp(self, data):
        if self.gui_time == 0.0:           # synchoronize HW time and GUI time at start up
            self.gui_time      = float(self.vars["HardwareTimestamp"].get())
            self.hwTimeOffset  = float(self.vars["HardwareTimestamp"].get())
            self.powerup_time  = 1000 * time.time()
            return self.gui_time
        else:
            self.gui_time = time.time() * 1000
            return self.gui_time  - self.powerup_time + self.hwTimeOffset



if __name__ == "__main__":
    root = tk.Tk()
    gui = CanSatGUI(root)
    sensor_data = {
        "temp": 26.3,
        "alt": 217,
        "press": 98000,
        "head": 325,
        "ax": 0.1, "ay": 0.1, "az": 9.8,
        "gx": 2, "gy": 1, "gz": 0.01,
        "mx": 120, "my": 120, "mz": 120,
        "sat": 4, "lat": 31.48, "lon": 74.27,
        "gpsAlt": 220,
        "HardwareTimestamp": 50.0  # example value
    }
    gui.update_fields(sensor_data)
    root.mainloop()
