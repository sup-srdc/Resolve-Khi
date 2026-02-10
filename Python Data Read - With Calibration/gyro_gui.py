from PIL import Image, ImageTk  # add at top with other imports
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time

class GyroGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gyro Monitor")
        self.root.configure(bg="black")  # dark background

        # --- Title ---
        title = tk.Label(root, text="Bias-Adjusted Gyro Rates",
                         font=("Helvetica", 18, "bold"),
                         fg="gold", bg="black")    # fg="#FFD700", bg="black")
        title.grid(row=0, column=0, columnspan=7, pady=(20, 25))

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
            top_frame, text="Bias-Adjusted Gyro Rates",
            font=("Arial", 22, "bold"), fg="gold", bg="black"
        )
        title.grid(row=0, column=1, sticky="nsew", padx=10)

        # Right Logo
        logo_right_img = Image.open("logo2.png").resize((110, 100))   # <-- second logo file
        logo_right = ImageTk.PhotoImage(logo_right_img)
        logo_right_label = tk.Label(top_frame, image=logo_right, bg="black")
        logo_right_label.image = logo_right
        logo_right_label.grid(row=0, column=2, sticky="e", padx=(10,40))




        # --- Internal angle state in degrees ---
        self.anglex = 0.0
        self.angley = 0.0
        self.anglez = 0.0
        self.last_time = 0.0 #time.time()

        # For Bias Removal From Gyro
        self.bias_x = 0.0
        self.bias_y = 0.0
        self.bias_z = 0.0
        self.calibrationSamples = 300
        self.performCalibration = True
        self.bias_samples = []   # holds first 300 samples
        self.calibrated = False  # flag once bias is ready


        # --- Styles ---
        self.box_font = ("Helvetica", 14, "bold")
        self.label_font = ("Helvetica", 12, "bold")
        self.box_bg = "#333333"
        self.box_fg = "#FFD700"
        self.box_bg = "black"
        self.box_fg = "gold"

        # --- Gyro Rates Row ---
        tk.Label(root, text="Gyro Rates (rad/s):", font=self.label_font,
                 fg=self.box_fg, bg="black").grid(row=1, column=0, sticky="w", padx=(20, 10))

        self.grx = self._make_box("gx", row=1, col=1)
        self.gry = self._make_box("gy", row=1, col=3)
        self.grz = self._make_box("gz", row=1, col=5)

        # --- Angles Row ---
        tk.Label(root, text="Angles (deg):", font=self.label_font,
                 fg=self.box_fg, bg="black").grid(row=2, column=0, sticky="w", padx=(20, 10), pady=(10, 10))

        self.anglex_box = self._make_box("Angle X", row=2, col=1)
        self.angley_box = self._make_box("Angle Y", row=2, col=3)
        self.anglez_box = self._make_box("Angle Z", row=2, col=5)

        # --- Reset Button ---
        self.reset_btn = tk.Button(root, text="Reset Angles",
                                   font=("Helvetica", 12, "bold"),
                                   bg="#404040", fg="white",
                                   command=self.reset_angles)
        self.reset_btn.grid(row=3, column=0, padx=(20, 10), pady=(120, 0), sticky="n")

        # --- Dials Row ---
        self.dials = []
        self._make_dial("Angle X", col=1)
        self._make_dial("Angle Y", col=3)
        self._make_dial("Angle Z", col=5)

    def _make_box(self, label, row, col):
        """Helper to create label + value box"""
        tk.Label(self.root, text=label + ":", font=self.label_font,
                 fg=self.box_fg, bg="black").grid(row=row, column=col, sticky="e", padx=(5, 5))
        box = tk.Label(self.root, text="0.0", width=8, height=1,
                       font=self.box_font, bg=self.box_bg,
                       fg=self.box_fg, relief="ridge")
        box.grid(row=row, column=col + 1, padx=(0, 15))
        return box

    def _make_dial(self, title, col):
        """Helper to create circular dial"""
        fig, ax = plt.subplots(figsize=(2.5, 2.5), subplot_kw={'aspect': 'equal'}, facecolor="black")
        ax.set_facecolor("black")
        ax.axis("off")

        # Outer circle
        circle = plt.Circle((0, 0), 1, color=self.box_fg, fill=False, linewidth=2)
        ax.add_artist(circle)

        # Ticks
        for ang in range(0, 360, 30):
            r_outer, r_inner = 0.95, 0.8
            x1, y1 = r_inner * np.cos(np.deg2rad(ang)), r_inner * np.sin(np.deg2rad(ang))
            x2, y2 = r_outer * np.cos(np.deg2rad(ang)), r_outer * np.sin(np.deg2rad(ang))
            ax.plot([x1, x2], [y1, y2], color=self.box_fg, linewidth=1.2)

        # Labels (0,90,180,270)
        for ang in [0, 90, 180, 270]:
            r = 1.35
            ax.text(r * np.cos(np.deg2rad(ang)), r * np.sin(np.deg2rad(ang)),
                    str(ang), ha="center", va="center",
                    fontsize=14, color=self.box_fg, fontweight="bold")

        # Needle
        needle, = ax.plot([0, 0], [0, 0.8], color="red", linewidth=2)

        # Title
        ax.text(0, -1.75, title, ha="center", va="center",
                fontsize=12, color=self.box_fg, fontweight="bold")

        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().grid(row=3, column=col, columnspan=2, pady=(15, 10))
        self.dials.append(needle)

    def reset_angles(self):
        self.anglex = 0.0
        self.angley = 0.0
        self.anglez = 0.0

    def update_state(self, gyro_rate, timestamp_hw):
            #"""Update rates and integrate angles"""

        now = timestamp_hw/1000  # ms to s conversion
        dt = now - self.last_time
        self.last_time = now

        gx, gy, gz = gyro_rate  # unpack

        if self.performCalibration:
            # --- Bias calculation phase ---
            if not self.calibrated:
                self.bias_samples.append((gx, gy, gz))
                if len(self.bias_samples) >= self.calibrationSamples:  # after 300 samples
                    # Compute average for each axis
                    self.bias_x = sum(s[0] for s in self.bias_samples) / self.calibrationSamples
                    self.bias_y = sum(s[1] for s in self.bias_samples) / self.calibrationSamples
                    self.bias_z = sum(s[2] for s in self.bias_samples) / self.calibrationSamples
                    self.calibrated = True
                    print(f"Bias calculated → X:{self.bias_x:.4f}, Y:{self.bias_y:.4f}, Z:{self.bias_z:.4f}")
                return  # do not update GUI until calibration is done

            # --- Apply bias correction ---
        gx -= self.bias_x
        gy -= self.bias_y
        gz -= self.bias_z

        # --- Integrate angles ---
        self.anglex += gx * dt * 57.3
        self.angley += gy * dt * 57.3
        self.anglez += gz * dt * 57.3



    def update_gyro(self, gyro_rate, timestamp_hw):
        gx, gy, gz = gyro_rate  # unpack
        # --- Update GUI boxes ---
        self.grx.config(text=f"{gx:.2f}")
        self.gry.config(text=f"{gy:.2f}")
        self.grz.config(text=f"{gz:.2f}")

        self.anglex_box.config(text=f"{self.anglex:.2f}")
        self.angley_box.config(text=f"{self.angley:.2f}")
        self.anglez_box.config(text=f"{self.anglez:.2f}")

        # Update needles
        if self.dials:
            self.dials[0].set_ydata([0, 0.8 * np.sin(self.anglex * np.pi / 180)])
            self.dials[0].set_xdata([0, 0.8 * np.cos(self.anglex * np.pi / 180)])

            self.dials[1].set_ydata([0, 0.8 * np.sin(self.angley * np.pi / 180)])
            self.dials[1].set_xdata([0, 0.8 * np.cos(self.angley * np.pi / 180)])

            self.dials[2].set_ydata([0, 0.8 * np.sin(self.anglez * np.pi / 180)])
            self.dials[2].set_xdata([0, 0.8 * np.cos(self.anglez * np.pi / 180)])

            # Force redraw
            for needle in self.dials:
                needle.figure.canvas.draw_idle()


if __name__ == "__main__":
    root = tk.Tk()
    app = GyroGUI(root)
    sensor_data = {
        "temp": 26.3,
        "alt": 125,
        "press": 98000,
        "head": 325,
        "ax": 0.1, "ay": 0.1, "az": 9.8,
        "gx": 2, "gy": 1, "gz": 0.01,
        "mx": 120, "my": 120, "mz": 120,
        "sat": -1, "lat": 400, "lon": 400,
        "gpsAlt": 100,
        "HardwareTimestamp": 50.0  # example value
    }
    gyro_rate = [0.2, 0.3, .1]
    app.update_gyro(gyro_rate, sensor_data["HardwareTimestamp"]);
    root.mainloop()
