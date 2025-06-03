import serial
import time

class SerialHandler:
    def __init__(self, port='COM6', baud=9600, timeout=1):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser = None

        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baud, timeout=self.timeout)
            time.sleep(3)  # Wait for Arduino to reset
            print(f"[INFO] Serial connection established on {self.port} at {self.baud} baud.")
        except serial.SerialException as e:
            raise RuntimeError(f"Failed to connect to {self.port}: {e}")

    def read_line(self):
        # Read a line from the serial port and decode it to string
        if self.ser and self.ser.in_waiting:
            return self.ser.readline().decode('utf-8').strip()
        return

    def send_command(self, command):
        # Send a string command to the serial device
        if self.ser:
            full_cmd = command.strip() + "\n"
            self.ser.write(full_cmd.encode('utf-8'))
            print(f"[TX] {full_cmd.strip()}")

    def close(self):
        # Safely close the serial port
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[INFO] Closed serial connection on {self.port}")
