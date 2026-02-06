import time
import logging
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection, ShdlcDevice
from sensirion_shdlc_driver.command import ShdlcCommand

logging.basicConfig(level=logging.DEBUG)

PORT = "/dev/ttyAMA0"   
BAUD = 115200

with ShdlcSerialPort(port=PORT, baudrate=BAUD) as sp:
    dev = ShdlcDevice(ShdlcConnection(sp), slave_address=0)

    # Stop (ignore failure)
    try:
        dev.execute(ShdlcCommand(id=0x01, data=b"", max_response_time=1.0))
    except Exception as e:
        print("Stop ignored:", repr(e))

    # Start measurement (per datasheet: [0x01, 0x03])
    dev.execute(ShdlcCommand(id=0x00, data=bytes([0x01, 0x03]), max_response_time=1.0))
    print("Started measurement.")
    time.sleep(2)

    # Poll read measured values (0x03)
    for i in range(10):
        raw = dev.execute(ShdlcCommand(id=0x03, data=b"", max_response_time=1.0))
        print(f"Read {i}: {len(raw)} bytes")
        time.sleep(1)
