# socket_plotter.py

import socket
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# === CONFIGURATION ===
HOST = 'localhost'
PORT = 12345
CSV_FILE = 'socket_datalog.csv'

# === CONNECT TO SENDER ===
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# === INITIALISE CSV ===
with open(CSV_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Timestamp', 'Temperature (C)', 'Soil Moisture'])

# === DATA STORAGE ===
temps, moistures, timestamps = [], [], []
buffer = ""

# === PLOTTING SETUP ===
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

def update(frame):
    global buffer
    try:
        data = client.recv(1024).decode('utf-8')
        buffer += data
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if line.startswith("T:"):
                parts = line.strip().split()
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

                # Trim to last 100 points
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
                ax1.set_title("Live Socket Data")
                ax1.tick_params(axis='x', rotation=45)
                ax2.tick_params(axis='x', rotation=45)
                fig.tight_layout()

    except Exception as e:
        print("Error:", e)

ani = animation.FuncAnimation(fig, update, interval=1000)
plt.show()

# === CLEANUP ===
client.close()
