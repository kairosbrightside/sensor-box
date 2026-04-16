import serial
import struct

class Plantower:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600, timeout=1)

    def read(self):
        while True:
            b1 = self.ser.read(1)
            if not b1:
                return None

            if b1 == b'\x42' and self.ser.read(1) == b'\x4D':
                frame = b'\x42\x4D' + self.ser.read(38)

                if len(frame) != 40:
                    return None

                checksum = sum(frame[0:38]) & 0xFFFF
                recvd = (frame[38] << 8) + frame[39]

                if checksum != recvd:
                    return None

                return {
                    "pm1": frame[10]*256 + frame[11],
                    "pm2_5": frame[12]*256 + frame[13],
                    "pm10": frame[14]*256 + frame[15],
                    "temp": struct.unpack(">h", frame[30:32])[0] / 10,
                    "rh": struct.unpack(">h", frame[32:34])[0] / 10,
                }