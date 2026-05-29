from gpiozero import DigitalOutputDevice
import time
import os
from config import CONTROL_DIR
# =========================
# CONFIG
# =========================

ZERO_FILE = os.path.join(CONTROL_DIR, "ZeroCall.txt")
HEATER_FILE = os.path.join(CONTROL_DIR, "HeaterRelay.txt")

ALERT_FILE = "/tmp/sensor_alert.txt"

# GPIO pins
ZERO_PIN = 21
HEATER_PIN = 20

# =========================
# SETUP
# =========================
zero_relay = DigitalOutputDevice(ZERO_PIN)
heater_relay = DigitalOutputDevice(HEATER_PIN)

last_alert = None


# =========================
# HELPERS
# =========================
def read_state(path):
    try:
        with open(path) as f:
            return f.read().strip() == "[1]"
    except:
        return False


def buzz_pause(n):
    for _ in range(n):
        time.sleep(1)
        zero_relay.on()
        time.sleep(0.1)
        zero_relay.off()
        time.sleep(0.1)
        zero_relay.on()
        time.sleep(0.1)
        zero_relay.off()


def buzz_continue(n):
    for _ in range(n):
        time.sleep(0.1)
        zero_relay.on()
        time.sleep(0.1)
        zero_relay.off()


def handle_alert():
    global last_alert

    if not os.path.exists(ALERT_FILE):
        return

    with open(ALERT_FILE) as f:
        cmd = f.read().strip()

    if cmd == last_alert:
        return

    last_alert = cmd

    if cmd.startswith("pause:"):
        n = int(cmd.split(":")[1])
        buzz_pause(n)

    elif cmd.startswith("continue:"):
        n = int(cmd.split(":")[1])
        buzz_continue(n)


# =========================
# MAIN LOOP
# =========================
while True:

    # --- Zero control ---
    zero_active = read_state(ZERO_FILE)

    # --- Heater control ---
    heater_on = read_state(HEATER_FILE)

    # Apply states
    zero_relay.value = zero_active
    heater_relay.value = heater_on

    # --- Alert handling ---
    handle_alert()

    time.sleep(0.5)