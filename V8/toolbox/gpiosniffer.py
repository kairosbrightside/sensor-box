from gpiozero import DigitalOutputDevice
from time import sleep

relay = DigitalOutputDevice(21)

relay.on()
print("HIGH")

relay.off()
print("LOW")