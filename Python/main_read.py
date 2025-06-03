import serial
import time
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from collections import deque

# === Configuration ===
PORT = 'COM11'          # Change as needed
BAUD = 9600
MAX_POINTS = 100

# === Serial Setup ===
ser = serial.Serial(PORT, BAUD)
time.sleep(2)

# === CSV Setup ===
csv_file = open("sensor_log.csv", mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "moisture", "temp_C"])

# === Buffers ===
moisture_vals = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
temp_vals = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
timestamps = deque(range(-MAX_POINTS, 0), maxlen=MAX_POINTS)

# === Plot Setup ===
plt.ion()
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

line1, = ax1.plot([], [], label='Moisture', color='tab:blue')
line2, = ax2.plot([], [], label='Temp (°C)', color='tab:red')

ax1.set_ylabel("Moisture (ADC)", color='tab:blue')
ax2.set_ylabel("Temperature (°C)", color='tab:red')
ax1.set_xlabel("Samples")
fig.suptitle("Real-Time Sensor Readings")
fig.legend(loc="upper left")
ax1.grid()

# === Live Loop ===
while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        now = datetime.now().isoformat(timespec='seconds')

        if line.startswith("MOIST:"):
            moisture = int(line.split(":")[1])
            moisture_vals.append(moisture)

        elif line.startswith("TEMP:"):
            temp = float(line.split(":")[1])
            temp_vals.append(temp)
            timestamps.append(timestamps[-1] + 1)

            # Save to CSV
            csv_writer.writerow([now, moisture_vals[-1], temp])
            csv_file.flush()

            # Update plot
            line1.set_data(timestamps, moisture_vals)
            line2.set_data(timestamps, temp_vals)

            ax1.set_xlim(timestamps[0], timestamps[-1])
            ax1.set_ylim(min(moisture_vals) - 10, max(moisture_vals) + 10)
            ax2.set_ylim(min(temp_vals) - 2, max(temp_vals) + 2)

            plt.pause(0.01)

    except KeyboardInterrupt:
        print("Interrupted.")
        break
    except Exception as e:
        print(f"Error: {e}")
        continue

ser.close()
csv_file.close()
