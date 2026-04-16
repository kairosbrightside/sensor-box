from gpiozero import DigitalOutputDevice
import time
import os

PIN = 26
FILE_PATH = '/media/particulatepi/data/PMoutputData/PlantowerRelay.txt'
DEFAULT_STATE = '[0]'
CHECK_INTERVAL = 5

relay = DigitalOutputDevice(PIN)

last_state = None

try:
    while True:

        if not os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'w') as f:
                f.write(DEFAULT_STATE)

        with open(FILE_PATH, 'r') as f:
            state = f.read().strip()

        if state in ['[0]', '[1]']:
            if state != last_state:
                if state == '[1]':
                    relay.on()
                else:
                    relay.off()

                last_state = state

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    pass

finally:
    relay.off()