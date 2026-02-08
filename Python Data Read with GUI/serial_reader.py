# serial_reader.py
import serial
import struct
import time
import threading

class SerialReader:
    HEADER = b'\xDD\xCC\xBB\xAA'
    PACKET_SIZE = 72
    FMT = '<f f f f f f f f f f f f f f f f f I'

    def __init__(self, port='COM3', baudrate=115200, callback=None):
        self.ser = serial.Serial(port, baudrate, timeout=0)
        self.buffer = bytearray()
        self.callback = callback
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self.serialport_thread, daemon=True)
        self.running = False

    def start(self):
        self.running = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self.ser.close()

    def serialport_thread(self):
        """Background thread: read serial continuously and fire callback per packet"""
        while not self._stop_event.is_set():
            n = self.ser.in_waiting
            if n:
                self.buffer += self.ser.read(n)

            # Try to extract packets
            while len(self.buffer) >= 4 + self.PACKET_SIZE:
                if self.buffer[0:4] == self.HEADER:
                    packet_bytes = self.buffer[4:4+self.PACKET_SIZE]
                    self.buffer = self.buffer[4+self.PACKET_SIZE:]

                    data = struct.unpack(self.FMT, packet_bytes)
                    (Temperature, Altitude, Pressure, Heading,
                     Xacc, Yacc, Zacc,
                     Angaccx, Angaccy, Angaccz,
                     Magx, Magy, Magz,
                     Sat, Lat, Longi, GPSAlt,
                     HardwareTimestamp) = data

                    sensor_data = {
                        "temp": Temperature,
                        "alt": Altitude,
                        "press": Pressure,
                        "head": Heading,
                        "ax": Xacc, "ay": Yacc, "az": Zacc,
                        "gx": Angaccx, "gy": Angaccy, "gz": Angaccz,
                        "mx": Magx, "my": Magy, "mz": Magz,
                        "sat": Sat, "lat": Lat, "lon": Longi,
                        "gpsAlt": GPSAlt,
                        "HardwareTimestamp": HardwareTimestamp,
                    }

                    if self.callback:
                        self.callback(sensor_data)

                else:
                    # not aligned, shift by 1
                    self.buffer = self.buffer[1:]

            time.sleep(0.001)  # tiny sleep to avoid pegging CPU

    def stop(self):
        self.running = False
        self.ser.close()