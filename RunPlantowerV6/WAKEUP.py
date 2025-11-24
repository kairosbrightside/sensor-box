import serial
import time

port = serial.Serial(
    "/dev/ttyAMA0",
    baudrate=9600,
    timeout=2
)

# Wake command for Plantower PMS5003/PMS5003ST
wake_cmd = bytes([0x42, 0x4D, 0xE1, 0x00, 0x01, 0x01, 0x71])

print("Sending wake command…")
port.write(wake_cmd)
time.sleep(1)

print("Listening for data…")
while True:
    data = port.read(32)   # should receive ~32 or 40 bytes per frame
    print(data)
