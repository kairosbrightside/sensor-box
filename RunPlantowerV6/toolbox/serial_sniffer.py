# sniffer

import serial
import RPi.GPIO

print('ttyAMA0')
ser = serial.Serial()
ser.port = '/dev/ttyAMA0' #ser.port = '/dev/serial1'
ser.baudrate = 9600
ser.stopbits = serial.STOPBITS_ONE
ser.parity = serial.PARITY_NONE
ser.bytesize = serial.EIGHTBITS
ser.timeout = 2

ser.open()
Instr = ser.read(100)
print(Instr)
ser.close()

print('ttyAMA1')
ser = serial.Serial()
ser.port = '/dev/ttyAMA1' #ser.port = '/dev/serial1'
ser.baudrate = 9600
ser.stopbits = serial.STOPBITS_ONE
ser.parity = serial.PARITY_NONE
ser.bytesize = serial.EIGHTBITS
ser.timeout = 2

ser.open()
Instr = ser.read(100)
print(Instr)
ser.close()
