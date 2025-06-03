import sys
import os
import csv
from datetime import datetime
from collections import deque
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from serial_handler import SerialHandler
from utils import (
    append_and_average,
    parse_sensor_line,
    get_iso_timestamp,
    clamp_servo_angle,
    log_sensor_data,
    update_plot,
    update_labels
)

class SerialPlotter(QtWidgets.QWidget):
    def __init__(self, port='COM6', baud=9600, max_points=20, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Sensor Plotter")
        self.resize(1000, 600)

        # Set up serial communication
        self.serial = SerialHandler(port, baud)
        self.max_points = max_points
        self.sample_count = 0
        self.batch_size = 10

        # Buffers for plotting
        self.moisture_vals = deque(maxlen=max_points)
        self.temp_vals = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)
        self.temp_batch = []
        self.moist_batch = []

        # Time tracking
        self.start_time = datetime.now()

        # CSV logging setup
        self.filename = f"sensor_log_{self.start_time.strftime('%Y%m%d_%H%M%S')}.csv"
        self.csv_file = open(self.filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["timestamp", "moisture", "temp_C"])

        self.setup_plot()
        self.setup_layout()
        self.setup_timer()

    def setup_plot(self):
        # Set up matplotlib plot
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        # Line objects for real-time update
        self.line1, = self.ax1.plot([], [], label='Moisture', color='tab:blue')
        self.line2, = self.ax2.plot([], [], label='Temp (°C)', color='tab:red')

        self.ax1.set_ylabel("Moisture (ADC)", color='tab:blue')
        self.ax2.set_ylabel("Temperature (°C)", color='tab:red')
        self.ax1.set_xlabel("Time (s)")
        self.ax1.grid()
        self.fig.suptitle("Real-Time Sensor Readings")
        self.fig.legend(loc="upper left")

    def setup_layout(self):
        # Arrange GUI layout
        main_layout = QHBoxLayout()
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.canvas)
        side_panel = QVBoxLayout()

        # Threshold input
        self.moisture_min_input = QLineEdit()
        self.moisture_max_input = QLineEdit()
        apply_button = QPushButton("Set Thresholds")
        apply_button.clicked.connect(self.set_thresholds)
        threshold_group = QGroupBox("Threshold Settings")
        threshold_layout = QVBoxLayout()
        self.moisture_min_input.setPlaceholderText("Moisture Min")
        self.moisture_max_input.setPlaceholderText("Moisture Max")
        threshold_layout.addWidget(QLabel("Enter Thresholds:"))
        threshold_layout.addWidget(self.moisture_min_input)
        threshold_layout.addWidget(self.moisture_max_input)
        threshold_layout.addWidget(apply_button)
        threshold_group.setLayout(threshold_layout)

        # Warning level input
        self.warning_min_input = QLineEdit()
        self.warning_max_input = QLineEdit()
        warning_button = QPushButton("Set Warnings")
        warning_button.clicked.connect(self.set_warnings)
        warning_group = QGroupBox("Warning Levels")
        warning_layout = QVBoxLayout()
        self.warning_min_input.setPlaceholderText("Warning Min")
        self.warning_max_input.setPlaceholderText("Warning Max")
        warning_layout.addWidget(QLabel("Enter Warning Levels:"))
        warning_layout.addWidget(self.warning_min_input)
        warning_layout.addWidget(self.warning_max_input)
        warning_layout.addWidget(warning_button)
        warning_group.setLayout(warning_layout)

        # Current reading labels
        self.moisture_label = QLabel("Moisture: ---")
        self.temp_label = QLabel("Temperature: ---")
        readout_group = QGroupBox("Current Readings")
        readout_layout = QVBoxLayout()
        readout_layout.addWidget(self.moisture_label)
        readout_layout.addWidget(self.temp_label)
        readout_group.setLayout(readout_layout)

        # Servo angle control
        self.servo_input = QLineEdit()
        self.servo_input.setPlaceholderText("Enter angle (0-180)")
        servo_button = QPushButton("Move Servo")
        servo_button.clicked.connect(lambda: self.send_servo_command(self.servo_input.text()))
        servo_group = QGroupBox("Servo Control")
        servo_layout = QVBoxLayout()
        servo_layout.addWidget(self.servo_input)
        servo_layout.addWidget(servo_button)
        servo_group.setLayout(servo_layout)

        # Assemble side panel
        side_panel.addWidget(threshold_group)
        side_panel.addWidget(warning_group)
        side_panel.addWidget(readout_group)
        side_panel.addWidget(servo_group)
        side_panel.addStretch()

        # Final layout assembly
        main_layout.addLayout(plot_layout, stretch=3)
        main_layout.addLayout(side_panel, stretch=1)
        self.setLayout(main_layout)

    def setup_timer(self):
        # Run update loop every 20ms
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(20)

    def set_thresholds(self):
        try:
            min_val = float(self.moisture_min_input.text())
            max_val = float(self.moisture_max_input.text())

            if max_val < min_val:
                raise ValueError("Max threshold must be greater than or equal to min threshold.")

            print(f"Thresholds set: Min={min_val}, Max={max_val}")
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Input Error", str(e))

    def set_warnings(self):
        try:
            min_warn = float(self.warning_min_input.text())
            max_warn = float(self.warning_max_input.text())

            if max_warn < min_warn:
                raise ValueError("Max warning level must be greater than or equal to min warning level.")

            print(f"Warnings set: Min={min_warn}, Max={max_warn}")
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Input Error", str(e))

    def send_servo_command(self, angle):
        # Clamp and send servo angle command
        try:
            angle = clamp_servo_angle(angle)
            self.serial.send_command(f"SET_SERVO:{angle}")
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a servo angle between 0 and 180.")

    def update_data(self):
        try:
            line = self.serial.read_line()
            if not line:
                return

            # Handle servo acknowledgement
            if line.startswith("ACK_SERVO:"):
                print(f"[RX] {line}")
                return

            parsed = parse_sensor_line(line)
            if not parsed:
                return

            moist, temp = parsed
            now = get_iso_timestamp()
            avg_temp, avg_moist = append_and_average(self.temp_batch, self.moist_batch, temp, moist, self.batch_size)

            if avg_temp is not None:
                self.temp_vals.append(avg_temp)
                self.moisture_vals.append(avg_moist)
                elapsed = (datetime.now() - self.start_time).total_seconds()
                self.timestamps.append(elapsed)

                log_sensor_data(self.csv_writer, now, avg_moist, avg_temp, self.csv_file)
                update_plot(self.ax1, self.ax2, self.canvas, self.line1, self.line2,
                            self.timestamps, self.moisture_vals, self.temp_vals)
                update_labels(self.moisture_label, self.temp_label, avg_moist, avg_temp)

        except Exception as e:
            print(f"[Error] {e}")

    def closeEvent(self, event):
        # Clean up on window close
        try:
            self.serial.close()
            self.csv_file.close()
            os.remove(self.filename)
            print(f"[INFO] Deleted temporary log file: {self.filename}")
        except Exception as e:
            print(f"[WARNING] Failed to delete CSV: {e}")
        event.accept()