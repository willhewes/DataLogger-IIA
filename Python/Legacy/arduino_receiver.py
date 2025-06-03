import time
import logging
import serial
import matplotlib.pyplot as plt
from collections import deque
import csv
from datetime import datetime

# --- Logging Setup ---
# Logging setup — use log.info(), log.error(), etc. instead of print()
# Example: log.info("Connected"), log.error("Something went wrong")
logging.basicConfig( 
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger() # Lest you use log.info() etc.

# --- Serial Reader ---
# Connects to an Arduino or serial device and prints/logs incoming lines
# Useful for reading sensor data or debug output from Arduino
# Change 'port' to your actual COM port (e.g. 'COM3' or '/dev/ttyUSB0')
def read_serial(port='COM3', baud=9600, timeout=1):
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=timeout)
        log.info(f"Connected to {port} at {baud} baud")
        time.sleep(2)  # wait for Arduino reset
        while True:
            line = ser.readline().decode().strip()
            if line:
                log.info(f"Received: {line}")
    except serial.SerialException as e:
        log.error(f"Serial error: {e}")


# --- Live Plotter ---
# Plots live data from a generator or stream
# Shows a fixed number of recent values, 
# auto-rescales, updates every 'interval' seconds

def live_plot(data_stream, title="Live Plot", interval=0.1, max_points=100):
    plt.ion()
    fig, ax = plt.subplots()
    y_data = deque(maxlen=max_points)
    x_data = deque(maxlen=max_points)
    line, = ax.plot([], [], lw=2)

    start_time = time.time()
    try:
        while True:
            value = next(data_stream)
            current_time = time.time() - start_time
            x_data.append(current_time)
            y_data.append(value)

            line.set_data(x_data, y_data)
            ax.relim()
            ax.autoscale_view()
            ax.set_title(title)
            plt.pause(interval)
    except KeyboardInterrupt:
        log.info("Plotting interrupted by user.")
        plt.close()


# --- Example Usage ---
def run_example():
    import random
    def fake_data():
        while True:
            yield random.uniform(0, 1)
    live_plot(fake_data(), title="Simulated Data")


#--- Append csv---
# Appends a timestamped row to a CSV file
# Automatically adds headers the first time the file is written
# Example: append_csv("data.csv", ["temp"], [23.7])
def append_csv(filename, headers, values):
    file_exists = False
    try:
        with open(filename, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp'] + headers)
        row = [datetime.now().isoformat(timespec='seconds')] + values
        writer.writerow(row)
