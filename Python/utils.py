from datetime import datetime

def append_and_average(temp_batch, moist_batch, new_temp, new_moist, batch_size=10):
    temp_batch.append(new_temp)
    moist_batch.append(new_moist)

    if len(temp_batch) >= batch_size:
        avg_temp = sum(temp_batch) / batch_size
        avg_moist = int(sum(moist_batch) / batch_size)
        temp_batch.clear()
        moist_batch.clear()
        return avg_temp, avg_moist
    return None, None

def parse_sensor_line(line):
    try:
        parts = line.split(",")
        if len(parts) != 2:
            return None
        moist = int(parts[0])
        temp = float(parts[1])
        return moist, temp
    except ValueError:
        return None

def get_iso_timestamp():
    return datetime.now().isoformat(timespec='seconds')

def get_current_time_string():
    """Returns the current time as a HH:MM:SS formatted string for clock display."""
    return datetime.now().strftime("%H:%M:%S")

def clamp_servo_angle(angle):
    angle = int(angle)
    if not 0 <= angle <= 180:
        raise ValueError("Angle must be between 0 and 180")
    return angle

def validate_range(min_val, max_val, label="value"):
    """Raises a ValueError if max_val is less than min_val."""
    if max_val < min_val:
        raise ValueError(f"Max {label} must be greater than or equal to min {label}.")

def generate_filename(prefix="sensor_log", ext="csv"):
    """Generates a timestamped filename."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.{ext}"

def log_sensor_data(writer, timestamp, moist, temp, file_handle):
    writer.writerow([timestamp, moist, temp])
    file_handle.flush()

def update_plot(ax1, ax2, canvas, line1, line2, timestamps, moist_vals, temp_vals):
    line1.set_data(timestamps, moist_vals)
    line2.set_data(timestamps, temp_vals)

    if len(timestamps) > 1:
        ax1.set_xlim(timestamps[0], timestamps[-1])
    else:
        ax1.set_xlim(0, 1)

    ax1.set_ylim(min(moist_vals) - 10, max(moist_vals) + 10)
    ax2.set_ylim(min(temp_vals) - 2, max(temp_vals) + 2)

    canvas.draw()

def update_labels(moisture_label, temp_label, moist, temp):
    moisture_label.setText(f"Moisture: {moist:.0f}")
    temp_label.setText(f"Temperature: {temp:.1f} °C")
