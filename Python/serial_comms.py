# serial_plotter.py

import serial
import time
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# === CONFIG ===
PORT = 'COM7'           # Replace with your actual Arduino port (e.g., '/dev/ttyUSB0' on Linux)
BAUDRATE = 9600
CSV_FILE = 'datalog.csv'

# === INITIALISE SERIAL AND FILE ===
ser = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(2)  # Wait for Arduino to reset

# Create CSV and write header
with open(CSV_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Timestamp', 'Temperature (C)', 'Soil Moisture'])

# === DATA STORAGE ===
temps, moistures, timestamps = [], [], []

# === PLOTTING SETUP ===
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

def update(frame):
    try:
        line = ser.readline().decode('utf-8').strip()
        if line.startswith("T:"):
            parts = line.split()
            temp = float(parts[0][2:])
            moisture = int(parts[1][2:])
            now = datetime.now()

            # Store data
            timestamps.append(now)
            temps.append(temp)
            moistures.append(moisture)

            # Write to CSV
            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([now.strftime("%Y-%m-%d %H:%M:%S"), temp, moisture])

            # Limit to last 100 points
            ts_trim = timestamps[-100:]
            temps_trim = temps[-100:]
            moist_trim = moistures[-100:]

            # Plot
            ax1.clear()
            ax2.clear()

            ax1.plot(ts_trim, temps_trim, color='red')
            ax2.plot(ts_trim, moist_trim, color='blue')

            ax1.set_ylabel("Temp (°C)")
            ax2.set_ylabel("Moisture")
            ax2.set_xlabel("Time")
            ax1.set_title("Live Arduino Data")
            ax1.tick_params(axis='x', rotation=45)
            ax2.tick_params(axis='x', rotation=45)
            fig.tight_layout()

    except Exception as e:
        print("Error:", e)

ani = animation.FuncAnimation(fig, update, interval=1000)
plt.show()

# === CLEANUP ON CLOSE ===
ser.close()
