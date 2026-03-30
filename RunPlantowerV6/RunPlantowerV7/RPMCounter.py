import RPi.GPIO as GPIO
import time
import os

# GPIO Pin where tachometer output is connected
TACH_PIN = 5  # Change to your actual GPIO pin
PULSES_PER_REV = 2  # Most PC fans output 2 pulses per revolution

# Path to save RPM log file
LOG_FILE_PATH = "/media/particulatepi/data/PMoutputData/BOX_PMS5003st_sn3_1Min.txt"

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(TACH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pulse_count = 0
rpm_list = []

def pulse_callback(channel):
    global pulse_count
    pulse_count += 1

# Attach interrupt to count pulses
GPIO.add_event_detect(TACH_PIN, GPIO.FALLING, callback=pulse_callback)

def calculate_rpm():
    global pulse_count, rpm_list
    
    while True:
        pulse_count = 0  # Reset counter
        time.sleep(1)  # Measure pulses over 1 second
        
        rpm = (pulse_count / PULSES_PER_REV) * 60 /100 # Convert to RPM
        rpm_list.append(rpm)
        
        if len(rpm_list) >= 60:  # Store 1-minute average
            avg_rpm = int(sum(rpm_list) / len(rpm_list))  # Convert to integer
            with open(LOG_FILE_PATH, "w") as f:  # Overwrite file instead of appending
                f.write(f"{avg_rpm}\n")
            rpm_list = []  # Reset list for next minute

try:
    calculate_rpm()
except KeyboardInterrupt:
    GPIO.cleanup()
