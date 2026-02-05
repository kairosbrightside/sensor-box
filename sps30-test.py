import time
import struct
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection, ShdlcDevice
from sensirion_shdlc_driver.command import ShdlcCommand

PORT = "/dev/ttyAMA4"   # UART on GPIO12/13
BAUD = 115200

def start_measurement(dev: ShdlcDevice):
    dev.execute(ShdlcCommand(id=0x00, data=bytes([0x01, 0x03]), max_response_time=0.2))

def stop_measurement(dev: ShdlcDevice):
    dev.execute(ShdlcCommand(id=0x01, data=b"", max_response_time=0.2))

def read_measurement(dev: ShdlcDevice):
    raw = dev.execute(ShdlcCommand(id=0x03, data=b"", max_response_time=0.2))
    if len(raw) != 40:
        return None
    vals = struct.unpack(">10f", raw)
    return vals  # (pm1.0, pm2.5, pm4.0, pm10, nc0.5, nc1.0, nc2.5, nc4.0, nc10, size)

with ShdlcSerialPort(port=PORT, baudrate=BAUD) as sp:
    dev = ShdlcDevice(ShdlcConnection(sp), slave_address=0)

    # stop first (in case it was already measuring)
    try:
        stop_measurement(dev)
    except Exception:
        pass

    start_measurement(dev)
    time.sleep(2)

    while True:
        v = read_measurement(dev)
        if v:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] PM2.5={v[1]:.2f} µg/m³  PM10={v[3]:.2f} µg/m³  size={v[9]:.2f} µm")
        time.sleep(1)
