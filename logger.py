#!/usr/bin/env python3
import serial
import time
import struct
import csv
import sys
from datetime import datetime

PT1_PORT = "/dev/ttyAMA0"   # GPIO14/15 (UART0)  Plantower #1
PT2_PORT = "/dev/ttyAMA2"   # GPIO0/1  (UART1)   Plantower #2  (your “other ones” port)
SPS_PORT = "/dev/ttyAMA4"   # GPIO12/13 (UART4)  SPS30

LOG_PATH = "sensor_log.csv"
DEBUG = True

def dbg(msg: str):
    """Timestamped debug print."""
    if DEBUG:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}", file=sys.stderr)

def open_serial(port: str, baud: int, timeout: float = 2.0) -> serial.Serial:
    """Open a serial port with helpful debug on failure."""
    try:
        s = serial.Serial(port=port, baudrate=baud, timeout=timeout)
        dbg(f"Opened {port} @ {baud} baud (timeout={timeout}s)")
        return s
    except Exception as e:
        dbg(f"ERROR opening {port} @ {baud}: {repr(e)}")
        raise

def port_sanity_check(port: str, baud: int, seconds: float = 1.0):
    """
    Reads raw bytes for a moment to prove the port is alive.
    For Plantower, you should usually see bytes streaming.
    For SPS30, you may see nothing until commands are sent (that's OK).
    """
    dbg(f"Sanity check {port} @ {baud} for {seconds:.1f}s...")
    try:
        s = open_serial(port, baud, timeout=0.2)
        start = time.time()
        total = 0
        while time.time() - start < seconds:
            chunk = s.read(256)
            total += len(chunk)
        s.close()
        dbg(f"Sanity check result {port}: read {total} bytes total")
    except Exception as e:
        dbg(f"Sanity check FAILED for {port}: {repr(e)}")


###############################################
#  Plantower Driver (PMS5003 / PMS5003ST)
###############################################
class Plantower:
    def __init__(self, port: str):
        self.port_name = port
        self.port = open_serial(port, 9600, timeout=2)

    def read_frame(self):
        """Reads a 40-byte Plantower ST frame. Returns dict or None."""
        # Find start bytes 0x42 0x4D
        while True:
            b1 = self.port.read(1)
            if not b1:
                return None
            if b1 == b'\x42':
                b2 = self.port.read(1)
                if b2 == b'\x4D':
                    frame = b1 + b2 + self.port.read(38)
                    if len(frame) != 40:
                        return None
                    return self.parse_frame(frame)

    def parse_frame(self, frame: bytes):
        """Parses PMS5003ST frame. Returns dict or None on checksum mismatch."""
        checksum = sum(frame[0:38]) & 0xFFFF
        recvd = (frame[38] << 8) + frame[39]
        if checksum != recvd:
            dbg(f"Plantower checksum mismatch on {self.port_name}: calc={checksum} recv={recvd}")
            return None

        data = {}
        data["pm1_0"]  = frame[10] * 256 + frame[11]
        data["pm2_5"]  = frame[12] * 256 + frame[13]
        data["pm10"]   = frame[14] * 256 + frame[15]

        data["gt0_3"]  = frame[16] * 256 + frame[17]
        data["gt0_5"]  = frame[18] * 256 + frame[19]
        data["gt1_0"]  = frame[20] * 256 + frame[21]
        data["gt2_5"]  = frame[22] * 256 + frame[23]
        data["gt5_0"]  = frame[24] * 256 + frame[25]
        data["gt10"]   = frame[26] * 256 + frame[27]

        data["hcho"]   = (frame[28] * 256 + frame[29]) / 1000.0

        temp_raw = struct.unpack(">h", frame[30:32])[0]
        rh_raw   = struct.unpack(">h", frame[32:34])[0]
        data["temp_C"] = temp_raw / 10.0
        data["rh"]     = rh_raw / 10.0

        return data


###############################################
#  SPS30 UART Driver (SHDLC)
###############################################
class SPS30_UART:
    START = 0x7E

    def __init__(self, port: str):
        self.port_name = port
        self.ser = open_serial(port, 115200, timeout=2)
        self.start_measurement()

    @staticmethod
    def checksum(byte_array: bytes) -> int:
        return (256 - (sum(byte_array) % 256)) % 256

    def send_cmd(self, cmd_id: int, payload: bytes = b''):
        frame = bytearray([self.START, cmd_id, len(payload)]) + payload
        frame.append(self.checksum(frame[1:]))
        self.ser.write(frame)

    def read_response(self):
        head = self.ser.read(1)
        if head != b'\x7E':
            return None
        cmd = self.ser.read(1)
        if not cmd:
            return None
        length_b = self.ser.read(1)
        if not length_b:
            return None
        length = length_b[0]
        data = self.ser.read(length)
        _checksum = self.ser.read(1)
        return data

    def start_measurement(self):
        # mass concentration mode
        self.send_cmd(0x00, b'\x01\x03')
        _ = self.read_response()  # optional; may be None depending on sensor timing

    def read(self):
        self.send_cmd(0x03)
        data = self.read_response()
        if not data:
            dbg(f"SPS30 no response on {self.port_name}")
            return None
        if len(data) != 60:
            dbg(f"SPS30 unexpected length on {self.port_name}: {len(data)} bytes")
            return None

        vals = struct.unpack(">ffffffffff", data[0:40])
        return {
            "pm1_0": vals[0],
            "pm2_5": vals[1],
            "pm4_0": vals[2],
            "pm10":  vals[3],
            "nc0_5": vals[4],
            "nc1_0": vals[5],
            "nc2_5": vals[6],
            "nc4_0": vals[7],
            "nc10":  vals[8],
            "avg_size": vals[9]
        }


def main():
    dbg("Starting sensor logger...")

    # Optional: quick sanity checks (uncomment if needed)
    # port_sanity_check(PT1_PORT, 9600, seconds=1.0)
    # port_sanity_check(PT2_PORT, 9600, seconds=1.0)
    # port_sanity_check(SPS_PORT, 115200, seconds=1.0)

    pt1 = Plantower(PT1_PORT)
    pt2 = Plantower(PT2_PORT)
    sps = SPS30_UART(SPS_PORT)

    header = [
        "timestamp",
        # PT1
        "pt1_pm1", "pt1_pm2_5", "pt1_pm10",
        "pt1_0_3", "pt1_0_5", "pt1_1_0",
        "pt1_2_5", "pt1_5_0", "pt1_10",
        "pt1_temp", "pt1_rh", "pt1_hcho",
        # PT2
        "pt2_pm1", "pt2_pm2_5", "pt2_pm10",
        "pt2_0_3", "pt2_0_5", "pt2_1_0",
        "pt2_2_5", "pt2_5_0", "pt2_10",
        "pt2_temp", "pt2_rh", "pt2_hcho",
        # SPS30
        "sps_pm1", "sps_pm2_5", "sps_pm4", "sps_pm10",
        "sps_nc0_5", "sps_nc1_0", "sps_nc2_5",
        "sps_nc4_0", "sps_nc10", "sps_size",
        # debug
        "ok_pt1", "ok_pt2", "ok_sps"
    ]

    with open(LOG_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        f.flush()

        while True:
            ts = datetime.now().isoformat(timespec="seconds")

            ok1 = ok2 = ok3 = False
            d1 = d2 = d3 = None

            # Read PT1
            try:
                d1 = pt1.read_frame()
                ok1 = d1 is not None
                if not ok1:
                    dbg("PT1 read returned None (timeout or checksum)")
            except Exception as e:
                dbg(f"PT1 ERROR: {repr(e)}")

            # Read PT2
            try:
                d2 = pt2.read_frame()
                ok2 = d2 is not None
                if not ok2:
                    dbg("PT2 read returned None (timeout or checksum)")
            except Exception as e:
                dbg(f"PT2 ERROR: {repr(e)}")

            # Read SPS30
            try:
                d3 = sps.read()
                ok3 = d3 is not None
            except Exception as e:
                dbg(f"SPS30 ERROR: {repr(e)}")

            # Fill row with blanks if something is missing (so you can see failures)
            def pt_row(d):
                if not d:
                    return [""] * 12
                return [
                    d["pm1_0"], d["pm2_5"], d["pm10"],
                    d["gt0_3"], d["gt0_5"], d["gt1_0"],
                    d["gt2_5"], d["gt5_0"], d["gt10"],
                    d["temp_C"], d["rh"], d["hcho"],
                ]

            def sps_row(d):
                if not d:
                    return [""] * 10
                return [
                    d["pm1_0"], d["pm2_5"], d["pm4_0"], d["pm10"],
                    d["nc0_5"], d["nc1_0"], d["nc2_5"],
                    d["nc4_0"], d["nc10"], d["avg_size"],
                ]

            row = [ts] + pt_row(d1) + pt_row(d2) + sps_row(d3) + [int(ok1), int(ok2), int(ok3)]

            writer.writerow(row)
            f.flush()

            dbg(f"Logged {ts} (pt1={ok1}, pt2={ok2}, sps={ok3})")
            time.sleep(1)


if __name__ == "__main__":
    main()
