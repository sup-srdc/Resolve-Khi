import tkinter as tk
from   tkinter import ttk
import serial.tools.list_ports
import sys

def select_com_port():
    """Open a black/gold themed dialog for COM port selection and return the chosen port"""
    port_root = tk.Tk()
    port_root.title("Select COM Port")
    port_root.configure(bg="black")

    ports = [port.device for port in serial.tools.list_ports.comports()]
    if not ports:
        print("No COM ports found!")
        sys.exit(1)

    port_var = tk.StringVar(value=ports[0])

    # --- Title ---
    tk.Label(
        port_root, text="Select COM Port",
        font=("Arial", 18, "bold"), fg="gold", bg="black"
    ).pack(pady=(20, 10))

    # --- Dropdown ---
    style = ttk.Style(port_root)
    style.theme_use("default")
    style.configure(
        "TCombobox",
        fieldbackground="black",
        background="black",
        foreground="black",
        selectforeground="black",
        selectbackground="black"
    )

    dropdown = ttk.Combobox(
        port_root, textvariable=port_var,
        values=ports, state="readonly", font=("Arial", 14, "bold"),
        justify="center"
    )
    dropdown.pack(pady=10, padx=20)

    # --- OK Button ---
    tk.Button(
        port_root, text="OK", command=port_root.quit,
        font=("Arial", 14, "bold"), fg="gold", bg="black",
        activebackground="black", activeforeground="gold",
        relief="raised", padx=20, pady=5
    ).pack(pady=(15, 20))

    port_root.mainloop()
    SERIAL_PORT = port_var.get()
    port_root.destroy()

    return SERIAL_PORT
