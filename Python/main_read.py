import serial
import time
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from collections import deque

# === Configuration ===
PORT = 'COM11'          # Change to your Arduino's COM port
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
moisture_vals = deque(maxlen=MAX_POINTS)
temp_vals = deque(maxlen=MAX_POINTS)
timestamps = deque(maxlen=MAX_POINTS)
sample_count = 0

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
            # Store moisture but delay plotting until TEMP arrives
            last_moisture = moisture

        elif line.startswith("TEMP:"):
            temp = float(line.split(":")[1])
            temp_vals.append(temp)
            moisture_vals.append(last_moisture if 'last_moisture' in locals() else 0)
            timestamps.append(sample_count)
            sample_count += 1

            # Save to CSV
            csv_writer.writerow([now, moisture_vals[-1], temp])
            csv_file.flush()

            # Update plot
            line1.set_data(timestamps, moisture_vals)
            line2.set_data(timestamps, temp_vals)

            ax1.set_xlim(max(0, sample_count - MAX_POINTS), sample_count)
            ax1.set_ylim(min(moisture_vals) - 10, max(moisture_vals) + 10)
            ax2.set_ylim(min(temp_vals) - 2, max(temp_vals) + 2)

            plt.pause(0.01)

    except KeyboardInterrupt:
        print("Interrupted by user.")
        break
    except Exception as e:
        print(f"Error: {e}")
        continue

ser.close()
csv_file.close()
import serial
import time
import csv
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from collections import deque

# === Configuration ===
PORT = 'COM11'          # Update this to match your Arduino port
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
moisture_vals = deque(maxlen=MAX_POINTS)
temp_vals = deque(maxlen=MAX_POINTS)
timestamps = deque(maxlen=MAX_POINTS)
sample_count = 0

# === FFT Filter ===
def fft_filter(signal, keep_fraction=0.1):
    if len(signal) < 8:
        return signal  # Not enough data for FFT
    n = len(signal)
    fft_vals = np.fft.fft(signal)
    cutoff = int(n * keep_fraction)
    fft_vals[cutoff:-cutoff] = 0
    filtered = np.fft.ifft(fft_vals)
    return filtered.real

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
            last_moisture = moisture

        elif line.startswith("TEMP:"):
            temp = float(line.split(":")[1])
            temp_vals.append(temp)
            moisture_vals.append(last_moisture if 'last_moisture' in locals() else 0)
            timestamps.append(sample_count)
            sample_count += 1

            # Save to CSV
            csv_writer.writerow([now, moisture_vals[-1], temp])
            csv_file.flush()

            # === Apply FFT Filtering ===
            smooth_temp = fft_filter(list(temp_vals), keep_fraction=0.1)
            smooth_moist = fft_filter(list(moisture_vals), keep_fraction=0.1)

            # === Plotting ===
            line1.set_data(timestamps, smooth_moist)
            line2.set_data(timestamps, smooth_temp)

            ax1.set_xlim(max(0, sample_count - MAX_POINTS), sample_count)
            ax1.set_ylim(min(smooth_moist) - 10, max(smooth_moist) + 10)
            ax2.set_ylim(min(smooth_temp) - 2, max(smooth_temp) + 2)

            plt.pause(0.01)

    except KeyboardInterrupt:
        print("Interrupted by user.")
        break
    except Exception as e:
        print(f"Error: {e}")
        continue

ser.close()
csv_file.close()
