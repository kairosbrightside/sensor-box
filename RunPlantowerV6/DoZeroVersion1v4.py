import RPi.GPIO as GPIO
import time
import os

# Constants
RELAY_PIN = 21
FILE_PATH = "/media/particulatepi/data/PMoutputData/ZeroCall.txt"

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)  # Start with relay OFF

try:
    while True:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r") as file:
                content = file.read().strip()
                if content == "[1]":
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                else:
                    GPIO.output(RELAY_PIN, GPIO.LOW)
        else:
            print("File not found:", FILE_PATH)
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Default to OFF if file missing

        time.sleep(5)

except KeyboardInterrupt:
    print("Program stopped by user.")

finally:
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.cleanup()