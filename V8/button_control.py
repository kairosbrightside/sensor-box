from gpiozero import Button
import time
import subprocess

import CheckOperationVersion1v3 as CheckOP
import StartUpWatchDogVersion1v3 as WatchDog

BUTTON_PIN = 4

# Create button with pull-up (matches your wiring)
button = Button(BUTTON_PIN, pull_up=True, hold_time=1)

press_start = None


def on_press():
    global press_start
    press_start = time.time()


def on_release():
    global press_start

    if press_start is None:
        return

    duration = time.time() - press_start
    press_start = None

    print(f"Button held for {duration:.1f} seconds")

    # Short hold → watchdog
    if 2 <= duration <= 5:
        print("Running watchdog...")
        WatchDog.doWatchDog(0)

    # Long hold → shutdown
    elif duration > 5:
        print("Shutting down...")
        CheckOP.AlertOPpause(5)
        subprocess.run(['sudo', 'shutdown', 'now'])

button.when_pressed = on_press
button.when_released = on_release

print("Button script running...")

# Keep script alive
while True:
    time.sleep(1)