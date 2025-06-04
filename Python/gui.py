import sys
import os
import csv
from datetime import datetime
from collections import deque, defaultdict
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, 
                            QVBoxLayout, QCheckBox, QScrollArea, QWidget, QComboBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from serial_handler import SerialHandler
from utils import (
    append_and_average,
    parse_sensor_line,
    get_iso_timestamp,
    get_current_time_string,
    clamp_servo_angle,
    validate_range,
    generate_filename,
    log_sensor_data,
    clamp_servo_angle,
    validate_range,
    generate_filename,
    log_sensor_data,
    update_plot,
    update_labels
)
from themes import apply_theme

class SerialPlotter(QtWidgets.QWidget):
    def __init__(self, port='COM6', baud=9600, max_points=20, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Sensor Plotter")
        self.resize(1200, 800)  # 增加窗口尺寸以适应更多图表

        # Set default theme
        self.theme = "light"

        # Set up serial communication
        self.serial = SerialHandler(port, baud)
        self.max_points = max_points
        self.sample_count = 0
        self.batch_size = 10

        # 使用字典管理多个数据流
        self.data_buffers = {
            'moisture': deque(maxlen=max_points),
            'temp_C': deque(maxlen=max_points),
        }
        self.batch_buffers = {
            'moisture': [],
            'temp_C': [],
        }
        self.timestamps = deque(maxlen=max_points)

        # 图表管理
        self.charts = {}
        self.active_charts = ['moisture', 'temp_C']  # 默认显示的图表

        # Time tracking
        self.start_time = datetime.now()

        # CSV logging setup
        self.filename = generate_filename()
        self.csv_file = open(self.filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["timestamp", "moisture", "temp_C"])

        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        
        # 左侧：图表区域（可滚动）
        plot_area = QVBoxLayout()
        
        # 图表容器（可滚动）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.chart_container)
        
        # 创建初始图表
        self.create_chart('moisture', "Moisture", "Moisture Level", 'tab:blue')
        self.create_chart('temp_C', "Temperature", "Temperature (°C)", 'tab:red')
        
        plot_area.addWidget(scroll_area)
        
        # 右侧：控制面板
        side_panel = QVBoxLayout()
        
        # 添加时钟
        self.clock_label = QLabel("Time: --:--:--")
        self.clock_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        side_panel.addWidget(self.clock_label)
        
        # 图表管理组
        chart_group = QGroupBox("Chart Management")
        chart_layout = QVBoxLayout()
        
        # 图表切换控制
        self.chart_checkboxes = {}
        for sensor in self.data_buffers.keys():
            cb = QCheckBox(f"Show {sensor} chart")
            cb.setChecked(sensor in self.active_charts)
            cb.stateChanged.connect(self.toggle_chart_visibility)
            chart_layout.addWidget(cb)
            self.chart_checkboxes[sensor] = cb
        
        # 添加新图表按钮
        self.new_chart_btn = QPushButton("Add New Chart")
        self.new_chart_btn.clicked.connect(self.add_new_chart)
        chart_layout.addWidget(self.new_chart_btn)
        
        chart_group.setLayout(chart_layout)
        side_panel.addWidget(chart_group)
        
        # 阈值设置组
        threshold_group = QGroupBox("Threshold Settings")
        threshold_layout = QVBoxLayout()
        self.moisture_min_input = QLineEdit()
        self.moisture_max_input = QLineEdit()
        apply_button = QPushButton("Set Thresholds")
        apply_button.clicked.connect(self.set_thresholds)
        self.moisture_min_input.setPlaceholderText("Moisture Min")
        self.moisture_max_input.setPlaceholderText("Moisture Max")
        threshold_layout.addWidget(QLabel("Enter Thresholds:"))
        threshold_layout.addWidget(self.moisture_min_input)
        threshold_layout.addWidget(self.moisture_max_input)
        threshold_layout.addWidget(apply_button)
        threshold_group.setLayout(threshold_layout)
        
        # 警告级别组
        warning_group = QGroupBox("Warning Levels")
        warning_layout = QVBoxLayout()
        self.warning_min_input = QLineEdit()
        self.warning_max_input = QLineEdit()
        warning_button = QPushButton("Set Warnings")
        warning_button.clicked.connect(self.set_warnings)
        self.warning_min_input.setPlaceholderText("Warning Min")
        self.warning_max_input.setPlaceholderText("Warning Max")
        warning_layout.addWidget(QLabel("Enter Warning Levels:"))
        warning_layout.addWidget(self.warning_min_input)
        warning_layout.addWidget(self.warning_max_input)
        warning_layout.addWidget(warning_button)
        warning_group.setLayout(warning_layout)
        
        # 读数显示组
        readout_group = QGroupBox("Current Readings")
        readout_layout = QVBoxLayout()
        self.moisture_label = QLabel("Moisture: ---")
        self.temp_label = QLabel("Temperature: ---")
        readout_layout.addWidget(self.moisture_label)
        readout_layout.addWidget(self.temp_label)
        readout_group.setLayout(readout_layout)
        
        # 舵机控制组
        servo_group = QGroupBox("Servo Control")
        servo_layout = QVBoxLayout()
        self.servo_input = QLineEdit()
        self.servo_input.setPlaceholderText("Enter angle (0-180)")
        servo_button = QPushButton("Move Servo")
        servo_button.clicked.connect(lambda: self.send_servo_command(self.servo_input.text()))
        servo_layout.addWidget(self.servo_input)
        servo_layout.addWidget(servo_button)
        servo_group.setLayout(servo_layout)
        
        # 主题切换按钮
        toggle_button = QPushButton("Toggle Theme")
        toggle_button.clicked.connect(self.toggle_theme)
        side_panel.addWidget(toggle_button)
        
        # 添加各个组到侧面板
        side_panel.addWidget(threshold_group)
        side_panel.addWidget(warning_group)
        side_panel.addWidget(readout_group)
        side_panel.addWidget(servo_group)
        side_panel.addStretch()
        
        # 应用初始主题
        apply_theme(self, self.theme)
        
        # 组装主布局
        main_layout.addLayout(plot_area, stretch=4)  # 图表区域占更多空间
        main_layout.addLayout(side_panel, stretch=1)
        self.setLayout(main_layout)

    def create_chart(self, sensor_id, title, ylabel, color):
        """创建新的图表"""
        # 创建图表组件
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # 初始化线条
        line, = ax.plot([], [], label=ylabel, color=color)
        
        # 配置图表
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Time (s)")
        ax.grid()
        fig.suptitle(title)
        fig.legend(loc="upper right")
        
        # 存储图表引用
        self.charts[sensor_id] = {
            'figure': fig,
            'canvas': canvas,
            'axis': ax,
            'line': line,
            'visible': True
        }
        
        # 添加到布局
        self.chart_layout.addWidget(canvas)

    def toggle_chart_visibility(self):
        """切换图表可见性"""
        for sensor_id, cb in self.chart_checkboxes.items():
            visible = cb.isChecked()
            chart = self.charts.get(sensor_id)
            if chart:
                chart['canvas'].setVisible(visible)
                chart['visible'] = visible

    def add_new_chart(self):
        """添加新图表对话框"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add New Chart")
        layout = QVBoxLayout(dialog)
        
        # 传感器选择
        layout.addWidget(QLabel("Select Sensor:"))
        sensor_combo = QComboBox()
        sensor_combo.addItems(list(self.data_buffers.keys()))
        layout.addWidget(sensor_combo)
        
        # 图表标题
        layout.addWidget(QLabel("Chart Title:"))
        title_edit = QLineEdit()
        layout.addWidget(title_edit)
        
        # Y轴标签
        layout.addWidget(QLabel("Y-Axis Label:"))
        ylabel_edit = QLineEdit()
        layout.addWidget(ylabel_edit)
        
        # 颜色选择
        layout.addWidget(QLabel("Line Color:"))
        color_combo = QComboBox()
        color_combo.addItems(['blue', 'red', 'green', 'purple', 'orange', 'brown'])
        layout.addWidget(color_combo)
        
        # 按钮
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sensor_id = sensor_combo.currentText()
            title = title_edit.text() or f"{sensor_id} Chart"
            ylabel = ylabel_edit.text() or sensor_id
            color = color_combo.currentText()
            
            # 创建新图表
            self.create_chart(sensor_id, title, ylabel, color)
            
            # 添加到复选框
            if sensor_id not in self.chart_checkboxes:
                cb = QCheckBox(f"Show {sensor_id} chart")
                cb.setChecked(True)
                cb.stateChanged.connect(self.toggle_chart_visibility)
                
                # 找到Chart Management组并添加新复选框
                for i in range(self.layout().count()):
                    widget = self.layout().itemAt(i).widget()
                    if isinstance(widget, QGroupBox) and widget.title() == "Chart Management":
                        layout = widget.layout()
                        # 在添加按钮前插入新复选框
                        layout.insertWidget(layout.count()-1, cb)
                        self.chart_checkboxes[sensor_id] = cb
                        break

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
        try:
            min_val = float(self.moisture_min_input.text())
            max_val = float(self.moisture_max_input.text())
            validate_range(min_val, max_val, "threshold")
            print(f"Thresholds set: Min={min_val}, Max={max_val}")
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Input Error", str(e))

    def set_warnings(self):
        try:
            min_warn = float(self.warning_min_input.text())
            max_warn = float(self.warning_max_input.text())
            validate_range(min_warn, max_warn, "warning level")
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
            
            # 更新批处理数据
            self.batch_buffers['moisture'].append(moist)
            self.batch_buffers['temp_C'].append(temp)
            
            # 检查是否达到批处理大小
            if len(self.batch_buffers['moisture']) >= self.batch_size:
                # 计算平均值
                avg_moist = sum(self.batch_buffers['moisture']) / self.batch_size
                avg_temp = sum(self.batch_buffers['temp_C']) / self.batch_size
                
                # 清空批处理缓冲区
                self.batch_buffers['moisture'].clear()
                self.batch_buffers['temp_C'].clear()
                
                # 更新数据缓冲区
                self.data_buffers['moisture'].append(avg_moist)
                self.data_buffers['temp_C'].append(avg_temp)
                
                elapsed = (datetime.now() - self.start_time).total_seconds()
                self.timestamps.append(elapsed)

                # 记录到CSV
                log_sensor_data(self.csv_writer, now, avg_moist, avg_temp, self.csv_file)
                
                # 更新标签
                update_labels(self.moisture_label, self.temp_label, avg_moist, avg_temp)
                
                # 更新所有可见图表
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
                            canvas.draw()

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