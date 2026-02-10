import csv
import time
import tkinter as tk
from  serial_port_button import select_com_port
from   serial_reader import SerialReader
import sys
from sensor_gui import CanSatGUI
from gyro_gui   import GyroGUI

BAUD_RATE = 115200
FLAG_WRITE_TO_FILE = 1
POLL_PERIOD  =      1

def main():
    SERIAL_PORT = select_com_port()    # adjust to your COM port
    
    # --- Tkinter root GUI setup for CanSat and Gyro ---
    root = tk.Tk()
    root.title("CanSat Monitor")
    canSat_monitor = CanSatGUI(root)

    # --- Separate window for Gyro GUI ---
    gyro_window = tk.Toplevel(root)
    gyro_window.title("Gyro Monitor")
    gyro_monitor = GyroGUI(gyro_window)

    # --- Setup CSV log file ---
    filename = time.strftime("cansat_log_%Y%m%d_%H%M%S.csv")
    logfile = open(filename, "w", newline="")
    writer = csv.DictWriter(
        logfile,
        fieldnames=[
            "HardwareTimestamp", "PythonTimestamp",
            "ax","ay","az", "gx","gy","gz",
            "mx","my","mz",
            "temp","press","alt","head",
            "sat","lat","lon","gpsAlt"
        ]
    )
    writer.count = 0
    if FLAG_WRITE_TO_FILE:
        writer.writeheader()

    # --- Packet callback ---
    last_update = 0
    def cansat_packet_callback(data):
        """Called from SerialReader thread when a packet arrives."""
        data["PythonTimestamp"] = canSat_monitor.getPythonTimestamp(data)
        
        # 1) Update GUI (schedule on Tkinter thread)
        if not hasattr(cansat_packet_callback, "last_update"):
            cansat_packet_callback.last_update = 0 


        canSat_monitor.update_state(data) 
        gyro_monitor.update_state( [data[key] for key in ["gx", "gy", "gz"]], data["HardwareTimestamp"] )   
        now = time.time()
        if now - cansat_packet_callback.last_update >= 0.05:  # ~20 Hz update
            cansat_packet_callback.last_update = now
            root.after(0, lambda: canSat_monitor.update_fields(data))
            root.after(0, lambda: gyro_monitor.update_gyro( [data[key] for key in ["gx", "gy", "gz"]], data["HardwareTimestamp"] ))
        
        # 2) Write to CSV
        if FLAG_WRITE_TO_FILE:
            writer.writerow(data)
            writer.count += 1
            if writer.count % 100 == 0:   # flush every 100 packets
                logfile.flush()
                # Add Python-side timestamp
        
        
        # Print for debugging
        print(
            f"T: {data['temp']:.2f} °C | "
            f"Alt: {data['alt']:.2f} m | "
            f"Acc: ({data['ax']:.2f}, {data['ay']:.2f}, {data['az']:.2f}) | "
            f"Gyro: ({data['gx']:.2f}, {data['gy']:.2f}, {data['gz']:.2f}) | "
            f"Head: {data['head']:.2f}° | "
            f"Sat: {data['sat']} | "
            f"TS: {data['HardwareTimestamp']}",
            end="\r",
            flush=True
        )


    # --- Close handler ---
    def on_close():
        print("Closing log file...")
        if not logfile.closed:
            logfile.close()

        print("Closing Serial Port ...")
        reader.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # --- Serial reader ---
    reader = SerialReader(port=SERIAL_PORT, baudrate=115200, callback=cansat_packet_callback)
    reader.start()

    # --- Tkinter loop keeps program alive ---
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Interrupted with Ctrl-C!")
    finally:
        if not logfile.closed:
            logfile.close()
        sys.exit(0)



def __init__(self, root):
    self.T0 = time.time()
    self.count = 0

if __name__ == "__main__":
    main()


