import sys
import serial
import csv
import time
import numpy as np
from datetime import datetime
from collections import deque
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SerialPlotter(QtWidgets.QWidget):
    def set_thresholds(self):
    # Future use: fetch and validate thresholds
        try:
            min_val = float(self.moisture_min_input.text())
            max_val = float(self.moisture_max_input.text())
            print(f"Thresholds set: Min={min_val}, Max={max_val}")
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter valid numeric thresholds.")

    def __init__(self, port='COM11', baud=9600, max_points=100, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Sensor Plotter")
        self.resize(1000, 600)

        # Config
        self.port = port
        self.baud = baud
        self.max_points = max_points
        self.sample_count = 0

        # Buffers
        self.moisture_vals = deque(maxlen=max_points)
        self.temp_vals = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)

        # Setup CSV logging
        filename = f"sensor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.csv_file = open(filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["timestamp", "moisture", "temp_C"])

        # Setup Serial
        try:
            self.ser = serial.Serial(self.port, self.baud)
            time.sleep(2)
        except serial.SerialException:
            QtWidgets.QMessageBox.critical(self, "Serial Error", f"Unable to open {self.port}")
            sys.exit(1)

        # Setup Plot
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        self.line1, = self.ax1.plot([], [], label='Moisture', color='tab:blue')
        self.line2, = self.ax2.plot([], [], label='Temp (°C)', color='tab:red')

        self.ax1.set_ylabel("Moisture (ADC)", color='tab:blue')
        self.ax2.set_ylabel("Temperature (°C)", color='tab:red')
        self.ax1.set_xlabel("Samples")
        self.ax1.grid()
        self.fig.suptitle("Real-Time Sensor Readings")
        self.fig.legend(loc="upper left")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
                # === Input Panel for Thresholds ===
        input_layout = QHBoxLayout()
        self.moisture_min_input = QLineEdit()
        self.moisture_max_input = QLineEdit()
        apply_button = QPushButton("Set Thresholds")

        self.moisture_min_input.setPlaceholderText("Moisture Min")
        self.moisture_max_input.setPlaceholderText("Moisture Max")

        input_layout.addWidget(QLabel("Thresholds:"))
        input_layout.addWidget(self.moisture_min_input)
        input_layout.addWidget(self.moisture_max_input)
        input_layout.addWidget(apply_button)

        # Dummy connection (future usage)
        apply_button.clicked.connect(self.set_thresholds)

        layout.addLayout(input_layout)

        self.setLayout(layout)

        # Timer for live update
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)

    def fft_filter(self, signal, keep_fraction=0.1):
        if len(signal) < 8:
            return signal
        n = len(signal)
        fft_vals = np.fft.fft(signal)
        cutoff = int(n * keep_fraction)
        fft_vals[cutoff:-cutoff] = 0
        return np.fft.ifft(fft_vals).real

    def update_data(self):
        try:
            line = self.ser.readline().decode('utf-8').strip()
            now = datetime.now().isoformat(timespec='seconds')

            # === Raw data accumulation ===
            if not hasattr(self, 'temp_batch'):
                self.temp_batch = []
                self.moist_batch = []
                self.batch_size = 5

            if line.startswith("MOIST:"):
                self.last_moisture = int(line.split(":")[1])

            elif line.startswith("TEMP:"):
                temp = float(line.split(":")[1])
                moist = getattr(self, 'last_moisture', 0)

                self.temp_batch.append(temp)
                self.moist_batch.append(moist)

                if len(self.temp_batch) >= self.batch_size:
                    # Compute averages
                    avg_temp = sum(self.temp_batch) / self.batch_size
                    avg_moist = sum(self.moist_batch) / self.batch_size

                    self.temp_vals.append(avg_temp)
                    self.moisture_vals.append(avg_moist)
                    self.timestamps.append(self.sample_count)
                    self.sample_count += 1

                    # Save to CSV
                    self.csv_writer.writerow([now, avg_moist, avg_temp])
                    self.csv_file.flush()

                    # Update plot
                    self.line1.set_data(self.timestamps, self.moisture_vals)
                    self.line2.set_data(self.timestamps, self.temp_vals)

                    self.ax1.set_xlim(max(0, self.sample_count - self.max_points), self.sample_count)
                    self.ax1.set_ylim(min(self.moisture_vals) - 10, max(self.moisture_vals) + 10)
                    self.ax2.set_ylim(min(self.temp_vals) - 2, max(self.temp_vals) + 2)

                    self.canvas.draw()

                    # Clear batch
                    self.temp_batch.clear()
                    self.moist_batch.clear()
        except Exception as e:
            print(f"[Error] {e}")


    def closeEvent(self, event):
        self.ser.close()
        self.csv_file.close()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SerialPlotter()
    window.show()
    sys.exit(app.exec())
