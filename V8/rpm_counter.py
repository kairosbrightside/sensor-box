from gpiozero import Button
import time

PIN = 17
PULSES_PER_REV = 2

count = 0

def tick():
    global count
    count += 1

tach = Button(PIN, pull_up=True, bounce_time=0.002)
tach.when_pressed = tick

while True:
    count = 0
    time.sleep(1)
    rpm = (count / PULSES_PER_REV) * 60
    print("RPM:", rpm)