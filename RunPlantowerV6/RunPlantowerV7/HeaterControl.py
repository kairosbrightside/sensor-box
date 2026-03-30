import os
import RPi.GPIO as GPIO
import time

# Constants
FILE_PATH = "/media/particulatepi/data/PMoutputData/HeaterRelay.txt"
RELAY_PIN = 20

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

def setup_file():
    """Create the file if it doesn't exist with default [0] value."""
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'w') as file:
            file.write('[0]')

def read_relay_state():
    """Read the value from the file and return it as an integer."""
    with open(FILE_PATH, 'r') as file:
        content = file.read().strip()
        if content == '[1]':
            return 1
        else:
            return 0

def control_relay(state):
    """Control the relay based on the state."""
    GPIO.output(RELAY_PIN, GPIO.HIGH if state == 1 else GPIO.LOW)

def main():
    try:
        setup_file()
        while True:
            state = read_relay_state()
            control_relay(state)
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
