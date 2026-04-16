from gpiozero import DigitalOutputDevice
import time
import os

RELAY_PIN = 21
FILE_PATH = "/media/piray/data/PMoutputData/ZeroCall.txt"

relay = DigitalOutputDevice(RELAY_PIN)

try:
    while True:
        state = False

        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r") as f:
                state = (f.read().strip() == "[1]")

        if state:
            relay.on()
        else:
            relay.off()

        time.sleep(5)

except KeyboardInterrupt:
    pass

finally:
    relay.off()

    