import serial
import time

port = serial.Serial("/dev/ttyAMA0", 9600, timeout=2)

wake_cmd = bytes([0x42, 0x4D, 0xE1, 0x00, 0x01, 0x01, 0x71])
start_cmd = bytes([0x42, 0x4D, 0xE2, 0x00, 0x00, 0x01, 0x71])

print("Sending wake + start commands…")
port.write(wake_cmd)
time.sleep(0.2)
port.write(start_cmd)
time.sleep(0.5)

print("Waiting for sensor output…")
while True:
    frame = port.read(40)
    print(frame)
