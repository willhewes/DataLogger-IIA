import serial
import time
import matplotlib.pyplot as plt
from collections import deque

# === Configuration ===
PORT = 'COM11'          # Replace with your Arduino's port
BAUD = 9600
MAX_POINTS = 100       # Number of points to show in the plot

# === Initialise Serial Connection ===
ser = serial.Serial(PORT, BAUD)
time.sleep(2)  # Give time for Arduino to reset

# === Rolling Buffers for Plotting ===
moisture_vals = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
temp_vals = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
timestamps = deque(range(-MAX_POINTS, 0), maxlen=MAX_POINTS)

# === Setup Plot ===
plt.ion()
fig, ax1 = plt.subplots()
line1, = ax1.plot([], [], label='Moisture', color='tab:blue')
line2, = ax1.plot([], [], label='Temp (°C)', color='tab:red')
ax1.set_ylim(0, 1024)
ax1.set_title("Real-Time Sensor Readings")
ax1.set_xlabel("Samples")
ax1.set_ylabel("ADC / Temp")
ax1.legend()
ax1.grid()

# === Update Plot Loop ===
while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line.startswith("MOIST:"):
            moisture = int(line.split(":")[1])
            moisture_vals.append(moisture)

        elif line.startswith("TEMP:"):
            temp = float(line.split(":")[1])
            temp_vals.append(temp)
            timestamps.append(timestamps[-1] + 1)

            # Update plot
            line1.set_data(timestamps, moisture_vals)
            line2.set_data(timestamps, temp_vals)
            ax1.set_xlim(timestamps[0], timestamps[-1])
            ax1.set_ylim(min(min(moisture_vals), min(temp_vals)) - 10,
                         max(max(moisture_vals), max(temp_vals)) + 10)
            plt.pause(0.01)

    except KeyboardInterrupt:
        print("Stopped by user.")
        break
    except Exception as e:
        print(f"Error: {e}")
        continue

ser.close()
