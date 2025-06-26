import RPi.GPIO as GPIO
import time
import os

# Configuration
PIN = 26  # GPIO pin to control
FILE_PATH = '/media/particulatepi/data/PMoutputData/PlantowerRelay.txt'
DEFAULT_STATE = '[0]'  # Default value if file doesn't exist
CHECK_INTERVAL = 5  # Seconds between checks

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

# Initialize current GPIO state
last_state = None

try:
    while True:
        # Create file if it doesn't exist
        if not os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'w') as f:
                f.write(DEFAULT_STATE)

        # Read file content
        with open(FILE_PATH, 'r') as f:
            state = f.read().strip()

        # Validate and apply state if it's different
        if state in ['[0]', '[1]']:
            if state != last_state:
                GPIO.output(PIN, GPIO.HIGH if state == '[1]' else GPIO.LOW)
                last_state = state

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    pass

except Exception:
    pass

finally:
    GPIO.cleanup()
