import time
import struct
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection, ShdlcDevice
from sensirion_shdlc_driver.command import ShdlcCommand

class SPS30:
    def __init__(self, port):
        self.sp = ShdlcSerialPort(port=port, baudrate=115200)
        self.dev = ShdlcDevice(ShdlcConnection(self.sp), slave_address=0)

        try:
            self.dev.execute(ShdlcCommand(0x01, b"", max_response_time=1))
        except:
            pass

        try:
            self.dev.execute(ShdlcCommand(0x00, bytes([1, 3]), max_response_time=1))
        except:
            pass

        time.sleep(2)

    def read(self):
        try:
            raw = self.dev.execute(ShdlcCommand(0x03, b"", max_response_time=1))

            if len(raw) < 40:
                return None

            vals = struct.unpack(">10f", raw[:40])

            return {
                "pm1": vals[0],
                "pm2_5": vals[1],
                "pm4": vals[2],
                "pm10": vals[3],
            }

        except:
            return None