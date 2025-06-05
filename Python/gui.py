import sys
import os
import csv
from datetime import datetime
from collections import deque, defaultdict
from PySide6 import QtWidgets, QtCore, QtMultimedia
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, 
                            QVBoxLayout, QCheckBox, QScrollArea, QWidget, QComboBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from serial_handler import SerialHandler
from utils import (
    append_and_average,
    parse_sensor_line,
    get_iso_timestamp,
    get_current_time_string,
    validate_range,
    generate_filename,
    log_sensor_data,
    validate_range,
    generate_filename,
    log_sensor_data,
    update_labels
)
from themes import apply_theme

class CollapsibleGroupBox(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(False) 
        self.toggled.connect(self.toggle_content)

        self.content_container = QWidget()
        self.content_container.setVisible(False)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.content_container)
        main_layout.setContentsMargins(0, 5, 0, 5)  

    def toggle_content(self, checked):
        self.content_container.setVisible(checked)

    def setLayout(self, layout):
        self.content_container.setLayout(layout)
        layout.setContentsMargins(5, 5, 5, 5)

class SerialPlotter(QtWidgets.QWidget):
    def __init__(self, port='COM6', baud=9600, max_points=20, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Sensor Plotter")
        self.resize(1200, 800)  # increase size of window for more charts

        # Set default theme
        self.theme = "light"

        # Set up serial communication
        self.serial = SerialHandler(port, baud)
        self.max_points = max_points
        self.sample_count = 0
        self.batch_size = 10

        # instead of signal variable per data stream now we use dictionary to manage different data stream from different sensor
        self.data_buffers = {
            'moisture': deque(maxlen=max_points),
            'temp_C': deque(maxlen=max_points),
        }
        self.batch_buffers = {
            'moisture': [],
            'temp_C': [],
        }
        self.timestamps = deque(maxlen=max_points)

        # Chart management
        self.charts = {}
        self.active_charts = ['moisture', 'temp_C']  # default chart

        # Time tracking
        self.start_time = datetime.now()

        # CSV logging setup
        self.filename = generate_filename()
        self.csv_file = open(self.filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["timestamp", "moisture", "temp_C"])

        # Warning system
        self.warnings = {
            'moisture': {'active': False, 'message': ''},
            'temp_C': {'active': False, 'message': ''}
        }
        
        # Warning  storage
        self.warning_thresholds = {
            'moisture': {'min': None, 'max': None},
            'temp_C': {'min': None, 'max': None}
        }
        # Threshold levels
        self.threshold_levels = {
            'moisture': {'min': None, 'max': None},
        }

        self.warning_playing = False

        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        
        # Left part: Chart area(scrollable)
        plot_area = QVBoxLayout()
        
        # chart container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.chart_container)
        
        # initialize charts
        self.create_chart('moisture', "Moisture", "Moisture Level", 'tab:blue')
        self.create_chart('temp_C', "Temperature", "Temperature (°C)", 'tab:red')
        
        plot_area.addWidget(scroll_area)
        
        # Wrap right-hand panel in a scroll area
        side_scroll_area = QScrollArea()
        side_scroll_area.setWidgetResizable(True)
        side_panel_container = QWidget()
        side_panel = QVBoxLayout(side_panel_container)
        side_scroll_area.setWidget(side_panel_container)
        
        # add clock
        self.clock_label = QLabel("Time: --:--:--")
        self.clock_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        side_panel.addWidget(self.clock_label)
        
        # chart management
        chart_group = CollapsibleGroupBox("Chart Management")
        chart_layout = QVBoxLayout()
        
        # chart toggle control
        self.chart_checkboxes = {}
        for sensor in self.data_buffers.keys():
            cb = QCheckBox(f"Show {sensor} chart")
            cb.setChecked(sensor in self.active_charts)
            cb.stateChanged.connect(self.toggle_chart_visibility)
            chart_layout.addWidget(cb)
            self.chart_checkboxes[sensor] = cb
        
        # add new chart
        self.new_chart_btn = QPushButton("Add New Chart")
        self.new_chart_btn.clicked.connect(self.add_new_chart)
        chart_layout.addWidget(self.new_chart_btn)
        
        chart_group.setLayout(chart_layout)
        side_panel.addWidget(chart_group)
        
        # ================== THRESHOLD SETTINGS ==================
        threshold_group = CollapsibleGroupBox("Threshold Settings")
        threshold_layout = QVBoxLayout()
        
        # Threshold controls for each sensor
        self.threshold_controls = {}
        for sensor in ['moisture']:  # Only add threshold controls for moisture
            sensor_group = QGroupBox(f"{sensor.capitalize()} Thresholds")
            sensor_layout = QVBoxLayout()
            
            min_input = QLineEdit()
            max_input = QLineEdit()
            apply_button = QPushButton(f"Set {sensor} Thresholds")
            apply_button.setProperty('sensor', sensor)  # Store sensor type
            apply_button.clicked.connect(self.set_thresholds)
            
            min_input.setPlaceholderText(f"{sensor} Min")
            max_input.setPlaceholderText(f"{sensor} Max")
            
            sensor_layout.addWidget(QLabel(f"Set thresholds for {sensor}:"))
            sensor_layout.addWidget(min_input)
            sensor_layout.addWidget(max_input)
            sensor_layout.addWidget(apply_button)
            
            sensor_group.setLayout(sensor_layout)
            threshold_layout.addWidget(sensor_group)
            
            # Save control references
            self.threshold_controls[sensor] = {
                'min_input': min_input,
                'max_input': max_input
            }
        
        threshold_group.setLayout(threshold_layout)
        
        # ================== WARNING SETTINGS ==================
        warning_group = CollapsibleGroupBox("Warning Settings")
        warning_layout = QVBoxLayout()
        
        # Warning controls for each sensor
        self.warning_controls = {}
        for sensor in self.data_buffers.keys():  # Include both moisture and temp_C in chart toggle
            sensor_group = QGroupBox(f"{sensor.capitalize()} Warnings")
            sensor_layout = QVBoxLayout()
            
            min_input = QLineEdit()
            max_input = QLineEdit()
            apply_button = QPushButton(f"Set {sensor} Warnings")
            apply_button.setProperty('sensor', sensor)  # Store sensor type
            apply_button.clicked.connect(self.set_warnings)
            
            min_input.setPlaceholderText(f"{sensor} Min Warning")
            max_input.setPlaceholderText(f"{sensor} Max Warning")
            
            sensor_layout.addWidget(QLabel(f"Set warnings for {sensor}:"))
            sensor_layout.addWidget(min_input)
            sensor_layout.addWidget(max_input)
            sensor_layout.addWidget(apply_button)
            
            sensor_group.setLayout(sensor_layout)
            warning_layout.addWidget(sensor_group)
            
            # Save control references
            self.warning_controls[sensor] = {
                'min_input': min_input,
                'max_input': max_input
            }
        
        warning_group.setLayout(warning_layout)
        
        # ================== WARNING DISPLAY ==================
        warning_display_group = QGroupBox("Active Warnings")
        warning_display_layout = QVBoxLayout()
        self.warning_display = QLabel("No active warnings")
        self.warning_display.setStyleSheet("""
            QLabel {
                color: black; 
                background-color: #f0f0f0; 
                padding: 10px; 
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                font-weight: normal;
            }
        """)
        self.warning_display.setWordWrap(True)
        self.warning_display.setMinimumHeight(80)
        warning_display_layout.addWidget(self.warning_display)
        warning_display_group.setLayout(warning_display_layout)
        
        # ================== READOUT DISPLAY ==================
        readout_group = QGroupBox("Current Readings")
        readout_layout = QVBoxLayout()
        self.moisture_label = QLabel("Moisture: ---")
        self.temp_label = QLabel("Temperature: ---")
        readout_layout.addWidget(self.moisture_label)
        readout_layout.addWidget(self.temp_label)
        readout_group.setLayout(readout_layout)

        # ================== SERVO CONTROL ==================
        servo_button = QPushButton("Water Plants")
        servo_button.clicked.connect(self.send_servo_command)

        servo_group = QGroupBox("Manual Watering")
        servo_layout = QVBoxLayout()
        servo_layout.addWidget(servo_button)
        servo_group.setLayout(servo_layout)
        
        # ================== THEME TOGGLE ==================
        toggle_button = QPushButton("Toggle Theme")
        toggle_button.clicked.connect(self.toggle_theme)
        side_panel.addWidget(toggle_button)
        
        # ================== ASSEMBLE SIDEPANEL ==================
        side_panel.addWidget(threshold_group)
        side_panel.addWidget(warning_group)
        side_panel.addWidget(warning_display_group)
        side_panel.addWidget(readout_group)
        side_panel.addWidget(servo_group)
        side_panel.addStretch()
        
        # apply initial theme
        apply_theme(self, self.theme)
        
        # assembly layout
        main_layout.addLayout(plot_area, stretch=4)
        main_layout.addWidget(side_scroll_area, stretch=1)
        self.setLayout(main_layout)

        self.resize_visible_charts()

    def resize_visible_charts(self):
        # Clear current chart layout
        while self.chart_layout.count():
            item = self.chart_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # Re-add visible charts with dynamic stretch
        visible_charts = [c['canvas'] for c in self.charts.values() if c['visible']]
        count = len(visible_charts)
        if count == 0:
            return

        for canvas in visible_charts:
            self.chart_layout.addWidget(canvas, stretch=1)

    def create_chart(self, sensor_id, title, ylabel, color):
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        line, = ax.plot([], [], label=ylabel, color=color)
        
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Time (s)")
        ax.grid()
        fig.suptitle(title)
        fig.legend(loc="upper right")
        
        self.charts[sensor_id] = {
            'figure': fig,
            'canvas': canvas,
            'axis': ax,
            'line': line,
            'visible': True
        }
    
    def toggle_chart_visibility(self):
        for sensor_id, cb in self.chart_checkboxes.items():
            visible = cb.isChecked()
            chart = self.charts.get(sensor_id)
            if chart:
                chart['canvas'].setVisible(visible)
                chart['visible'] = visible

        self.resize_visible_charts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_visible_charts()

    def add_new_chart(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add New Chart")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Select Sensor:"))
        sensor_combo = QComboBox()
        sensor_combo.addItems(list(self.data_buffers.keys()))
        layout.addWidget(sensor_combo)
        
        layout.addWidget(QLabel("Chart Title:"))
        title_edit = QLineEdit()
        layout.addWidget(title_edit)
        
        layout.addWidget(QLabel("Y-Axis Label:"))
        ylabel_edit = QLineEdit()
        layout.addWidget(ylabel_edit)
        
        layout.addWidget(QLabel("Line Color:"))
        color_combo = QComboBox()
        color_combo.addItems(['blue', 'red', 'green', 'purple', 'orange', 'brown'])
        layout.addWidget(color_combo)
        
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            sensor_id = sensor_combo.currentText()
            title = title_edit.text() or f"{sensor_id} Chart"
            ylabel = ylabel_edit.text() or sensor_id
            color = color_combo.currentText()
            
            self.create_chart(sensor_id, title, ylabel, color)
            
            if sensor_id not in self.chart_checkboxes:
                cb = QCheckBox(f"Show {sensor_id} chart")
                cb.setChecked(True)
                cb.stateChanged.connect(self.toggle_chart_visibility)
                
                for i in range(self.layout().count()):
                    widget = self.layout().itemAt(i).widget()
                    if isinstance(widget, QGroupBox) and widget.title() == "Chart Management":
                        layout = widget.layout()
                        layout.insertWidget(layout.count()-1, cb)
                        self.chart_checkboxes[sensor_id] = cb
                        break

            # Initialize warning system for new sensor
            if sensor_id not in self.warnings:
                self.warnings[sensor_id] = {'active': False, 'message': ''}
                self.warning_thresholds[sensor_id] = {'min': None, 'max': None}

    def setup_timer(self):
        # Run update loop every 20ms
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(20)

        # Clock update timer (once per second)
        self.clock_timer = QtCore.QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

    def update_clock(self):
        self.clock_label.setText(f"Time: {get_current_time_string()}")

    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        apply_theme(self, self.theme)

    def set_thresholds(self):
        sensor = self.sender().property('sensor')
        if sensor != "moisture":
            return

        try:
            # Get the sensor type from the button that triggered the event
            sensor = self.sender().property('sensor')
            
            min_val = float(self.threshold_controls[sensor]['min_input'].text())
            max_val = float(self.threshold_controls[sensor]['max_input'].text())
            validate_range(min_val, max_val, "threshold")
            # Save internal GUI-side thresholds
            self.threshold_levels[sensor]['min'] = min_val
            self.threshold_levels[sensor]['max'] = max_val


            # Format name for Arduino
            arduino_name = "moisture"

            # Construct and send threshold command to Arduino
            command = f"SET_THRESH {arduino_name} {min_val:.2f} {max_val:.2f}"
            self.serial.send_command(command)
            print(f"Sent to Arduino: {command}")

        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Input Error", str(e))

    def set_warnings(self):
        try:
            # Get the sensor type from the button that triggered the event
            sensor = self.sender().property('sensor')
            
            min_warn = float(self.warning_controls[sensor]['min_input'].text())
            max_warn = float(self.warning_controls[sensor]['max_input'].text())
            validate_range(min_warn, max_warn, "warning level")
            
            # Save warning thresholds
            self.warning_thresholds[sensor]['min'] = min_warn
            self.warning_thresholds[sensor]['max'] = max_warn
            
            # Save warning thresholds
            self.warning_thresholds[sensor]['min'] = min_warn
            self.warning_thresholds[sensor]['max'] = max_warn

            # Format the sensor name for Arduino
            arduino_name = "temp_C" if sensor == "temp_C" else "moisture"

            # Construct command string
            command = f"SET_WARN {arduino_name} {min_warn:.2f} {max_warn:.2f}"
            self.serial.send_command(command)
            print(f"Sent to Arduino: {command}")

        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Input Error", str(e))

    def send_servo_command(self):
        # Send servo angle command
        self.serial.send_command("STEP_SERVO")

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
            
            # update batch processing data
            self.batch_buffers['moisture'].append(moist)
            self.batch_buffers['temp_C'].append(temp)
            
            # check whether they reach batch size for processing
            if len(self.batch_buffers['moisture']) >= self.batch_size:
                # calculate average
                avg_moist = sum(self.batch_buffers['moisture']) / self.batch_size
                avg_temp = sum(self.batch_buffers['temp_C']) / self.batch_size
                
                # clear batch_buffer
                self.batch_buffers['moisture'].clear()
                self.batch_buffers['temp_C'].clear()
                
                # update data buffer
                self.data_buffers['moisture'].append(avg_moist)
                self.data_buffers['temp_C'].append(avg_temp)
                
                elapsed = (datetime.now() - self.start_time).total_seconds()
                self.timestamps.append(elapsed)

                # log to CSV
                log_sensor_data(self.csv_writer, now, avg_moist, avg_temp, self.csv_file)
                
                # update label
                update_labels(self.moisture_label, self.temp_label, avg_moist, avg_temp)
                
                # update all visible chart
                for sensor_id, chart in self.charts.items():
                    if chart['visible']:
                        data = self.data_buffers.get(sensor_id)
                        if data:
                            line = chart['line']
                            ax = chart['axis']
                            canvas = chart['canvas']
                            
                            line.set_data(self.timestamps, data)

                            if len(self.timestamps) > 1:
                                ax.set_xlim(self.timestamps[0], self.timestamps[-1])
                            else:
                                ax.set_xlim(0, 1)

                            ax.set_ylim(min(data) - 10, max(data) + 10)

                            # Fix cropping by forcing layout adjustment
                            chart['figure'].tight_layout()
                            canvas.draw()
                
                # Check for warnings
                self.check_warnings()

        except Exception as e:
            print(f"[Error] {e}")

    def check_warnings(self):
        active_warnings = []
        warning_occurred = False
        
        # Check warning status for each sensor
        for sensor in self.data_buffers.keys():
            # Get current value and warning settings
            current_value = self.data_buffers[sensor][-1] if self.data_buffers[sensor] else None
            min_warn = self.warning_thresholds[sensor]['min']
            max_warn = self.warning_thresholds[sensor]['max']
            
            # If warning values are set and we have current value
            if min_warn is not None and max_warn is not None and current_value is not None:
                # Check if below minimum warning
                if current_value < min_warn:
                    self.warnings[sensor]['active'] = True
                    message = f"{sensor.capitalize()} is too low: {current_value:.1f} < {min_warn:.1f}"
                    self.warnings[sensor]['message'] = message
                    active_warnings.append(message)
                    warning_occurred = True
                # Check if above maximum warning
                elif current_value > max_warn:
                    self.warnings[sensor]['active'] = True
                    message = f"{sensor.capitalize()} is too high: {current_value:.1f} > {max_warn:.1f}"
                    self.warnings[sensor]['message'] = message
                    active_warnings.append(message)
                    warning_occurred = True
                # Value is within normal range
                else:
                    self.warnings[sensor]['active'] = False
                    self.warnings[sensor]['message'] = ''
            else:
                self.warnings[sensor]['active'] = False
                self.warnings[sensor]['message'] = ''
        
        # Play warning sound if any warning is active
        if warning_occurred and not self.warning_playing:
            QtWidgets.QApplication.beep()
            self.warning_playing = True
        elif not warning_occurred and self.warning_playing:
            self.warning_playing = False
        
        # Update warning display
        if active_warnings:
            warning_text = "⚠️ WARNING! ⚠️\n" + "\n".join(active_warnings)
            self.warning_display.setText(warning_text)
            self.warning_display.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.warning_display.setStyleSheet("""
                QLabel {
                    color: #b30000; 
                    background-color: #ffe6e6; 
                    padding: 10px; 
                    border: 2px solid #ff6666;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        else:
            self.warning_display.setText("No active warnings")
            self.warning_display.setStyleSheet("""
                QLabel {
                    color: black; 
                    background-color: #f0f0f0; 
                    padding: 10px; 
                    border: 1px solid #d0d0d0;
                    border-radius: 5px;
                    font-weight: normal;
                }
            """)

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