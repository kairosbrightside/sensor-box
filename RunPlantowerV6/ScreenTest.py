import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os

# File paths
file_sn1 = "/media/particulatepi/data/PMoutputData/BOX_PMS5003st_sn1_1Min.txt"
file_sn2 = "/media/particulatepi/data/PMoutputData/BOX_PMS5003st_sn2_1Min.txt"
file_rpm = "/media/particulatepi/data/PMoutputData/BOX_PMS5003st_sn3_1Min.txt"
zero_call_file = "/media/particulatepi/data/PMoutputData/ZeroCall.txt"

# Data labels
labels = [
    "Year", "Month", "Day", "Hour", "Minute", "Second",
    "apm1_0", "apm2_5", "apm10", "pm1_0", "pm2.5", "pm10",
    "gt03um", "gt05um", "gt1_0um", "gt2_5um", "gt5_0um", "gt10um",
    "form", "Temperature", "Relative Humidity (%)", "zero", "code_version", "sn"
]

# Display configuration
display_labels = [
    "Year", "Month", "Day", "Hour",
    "Temperature", "Relative Humidity (%)", "pm2.5", "gt03um", "zero"
]
display_indices = [labels.index(label) for label in display_labels]

# Zeroing time window
auto_zero_start = (10, 50)
auto_zero_end = (11, 10)

# GUI setup
root = tk.Tk()
root.title("Sensor Data Display")
root.geometry("2200x1200")

frame = ttk.Frame(root, padding=20)
frame.grid(row=0, column=0, sticky="nsew")

manual_zero_var = tk.IntVar()

def safe_read_file(path):
    try:
        with open(path, "r") as f:
            return f.readlines()
    except:
        return []

def read_latest_data(file_path):
    lines = safe_read_file(file_path)
    if lines:
        return lines[-1].strip().split(",")
    return ["N/A"] * len(labels)

def read_rpm_data(file_path):
    lines = [line.strip() for line in safe_read_file(file_path) if line.strip().isdigit()]
    return lines[-1] if lines else "N/A"

def save_zero_state():
    try:
        with open(zero_call_file, "w") as f:
            f.write(f"[{manual_zero_var.get()}]")  # Ensure brackets are included
        print(f"Zero state saved: [{manual_zero_var.get()}]")
    except Exception as e:
        print(f"Error saving zero state: {e}")

def check_auto_zero():
    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute
    start = auto_zero_start[0] * 60 + auto_zero_start[1]
    end = auto_zero_end[0] * 60 + auto_zero_end[1]

    in_window = start <= now_minutes <= end

    if in_window:
        if manual_zero_var.get() != 1:
            manual_zero_var.set(1)
            save_zero_state()
        manual_zero_checkbox.state(['disabled'])
    else:
        manual_zero_checkbox.state(['!disabled'])

        # If auto-zero was active and hasn't been manually unchecked,
        # reset it after the window ends
        if manual_zero_var.get() == 1:
            manual_zero_var.set(0)
            save_zero_state()

    root.after(600000, check_auto_zero)  # Check every 10 minutes

def format_value(label, value):
    try:
        if label == "Temperature":
            return f"{(float(value) * 0.1 - 273.1):.1f}"
        elif label == "Relative Humidity (%)":
            return f"{float(value) * 0.1:.1f}"
        else:
            return value
    except:
        return "N/A"

def update_display():
    sn1 = read_latest_data(file_sn1)
    sn2 = read_latest_data(file_sn2)
    rpm = read_rpm_data(file_rpm)

    for idx, data_i in enumerate(display_indices):
        label = labels[data_i]
        val1 = sn1[data_i] if data_i < len(sn1) else "N/A"
        val2 = sn2[data_i] if data_i < len(sn2) else "N/A"

        val1 = format_value(label, val1)
        val2 = format_value(label, val2)

        label_widgets[idx].config(text=f"{label}:")
        value_widgets_sn1[idx].config(text=val1)
        value_widgets_sn2[idx].config(text=val2)

    rpm_label.config(text="RPM:")
    rpm_value_widget.config(text=rpm)
    try:
        rpm_int = int(rpm)
        rpm_value_widget.config(foreground="green" if rpm_int >= 1000 else "red")
    except:
        rpm_value_widget.config(foreground="gray")

    #last_updated_label.config(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    root.after(5000, update_display)

def update_clock():
    system_time_label.config(text=f"System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    root.after(1000, update_clock)

# GUI layout
ttks = ttk.Label
header = [("Parameter", 0), ("SNA", 1), ("SNB", 2)]
for title, col in header:
    ttks(frame, text=title, font=("Arial", 30, "bold", "underline")).grid(row=0, column=col, padx=10, pady=10)

label_widgets, value_widgets_sn1, value_widgets_sn2 = [], [], []
for i, idx in enumerate(display_indices):
    label_widgets.append(ttks(frame, text="", font=("Arial", 24)))
    label_widgets[-1].grid(row=i+1, column=0, sticky="w", padx=5, pady=2)

    value_widgets_sn1.append(ttks(frame, text="N/A", font=("Arial", 24)))
    value_widgets_sn1[-1].grid(row=i+1, column=1, padx=5, pady=2)

    value_widgets_sn2.append(ttks(frame, text="N/A", font=("Arial", 24)))
    value_widgets_sn2[-1].grid(row=i+1, column=2, padx=5, pady=2)

# RPM
rpm_label = ttks(frame, text="RPM:", font=("Arial", 30, "bold", "underline"))
rpm_label.grid(row=0, column=4, padx=20, pady=10)

rpm_value_widget = ttks(frame, text="N/A", font=("Arial", 30))
rpm_value_widget.grid(row=0, column=5, padx=5, pady=5)

# Style for larger checkbox
style = ttk.Style()
style.configure("Big.TCheckbutton", font=("Arial", 30))

# Manual zero checkbox (enlarged)
manual_zero_checkbox = ttk.Checkbutton(
    frame, text="Manual Zero", variable=manual_zero_var,
    command=save_zero_state, style="Big.TCheckbutton"
)
manual_zero_checkbox.grid(row=0, column=6, padx=40, pady=20)

# Time info
last_updated_label = ttks(frame, text="", font=("Arial", 24, "italic"))
last_updated_label.grid(row=len(display_indices)+2, column=0, columnspan=3, sticky="w", padx=5, pady=10)

system_time_label = ttks(frame, text="", font=("Arial", 24, "italic"))
system_time_label.grid(row=len(display_indices)+3, column=0, columnspan=3, sticky="w", padx=5, pady=5)

# Scheduled zero times
ttks(frame, text=f"Scheduled Zero Start: {auto_zero_start[0]:02d}:{auto_zero_start[1]:02d}", font=("Arial", 24)).grid(
    row=len(display_indices)+4, column=0, columnspan=3, sticky="w", padx=5, pady=2
)

ttks(frame, text=f"Scheduled Zero End: {auto_zero_end[0]:02d}:{auto_zero_end[1]:02d}", font=("Arial", 24)).grid(
    row=len(display_indices)+5, column=0, columnspan=3, sticky="w", padx=5, pady=2
)

# Start everything
update_display()
update_clock()
check_auto_zero()
root.mainloop()
