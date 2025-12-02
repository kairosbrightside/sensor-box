#!/usr/bin/env python3
import serial
import time
import struct
import csv
from datetime import datetime

###############################################
#  Plantower Driver (PMS5003 / PMS5003ST)
###############################################
class Plantower:
    def __init__(self, port):
        self.port = serial.Serial(
            port=port,
            baudrate=9600,
            timeout=2
        )

    def read_frame(self):
        """Reads a 32-byte or 40-byte Plantower frame."""
        while True:
            b1 = self.port.read(1)
            if b1 == b'\x42':
                b2 = self.port.read(1)
                if b2 == b'\x4D':
                    # Plantower ST = 40 byte frame
                    frame = b1 + b2 + self.port.read(38)
                    if len(frame) == 40:
                        return self.parse_frame(frame)

    def parse_frame(self, frame):
        """Parses PMS5003ST frame."""
        checksum = sum(frame[0:38])
        recvd = (frame[38] << 8) + frame[39]

        if checksum != recvd:
            return None

        data = {}

        # Frame fields (see Plantower PMS5003ST manual)
        data["pm1_0"]  = frame[10] * 256 + frame[11]
        data["pm2_5"]  = frame[12] * 256 + frame[13]
        data["pm10"]   = frame[14] * 256 + frame[15]

        # Particle counts
        data["gt0_3"]  = frame[16] * 256 + frame[17]
        data["gt0_5"]  = frame[18] * 256 + frame[19]
        data["gt1_0"]  = frame[20] * 256 + frame[21]
        data["gt2_5"]  = frame[22] * 256 + frame[23]
        data["gt5_0"]  = frame[24] * 256 + frame[25]
        data["gt10"]   = frame[26] * 256 + frame[27]

        # Temperature & RH (ST only)
        temp_raw = struct.unpack(">h", frame[30:32])[0]
        rh_raw   = struct.unpack(">h", frame[32:34])[0]

        data["temp_C"] = temp_raw / 10.0
        data["rh"]     = rh_raw / 10.0

        # Formaldehyde (ST)
        data["hcho"] = (frame[28] * 256 + frame[29]) / 1000.0

        return data


###############################################
#  SPS30 UART Driver (SHDLC)
#  On UART5 (GPIO0/1 = ID_SD/ID_SC)
###############################################
class SPS30_UART:
    START = 0x7E

    def __init__(self, port="/dev/ttyAMA5"):
        self.ser = serial.Serial(port=port, baudrate=115200, timeout=2)
        self.start_measurement()

    def checksum(self, byte_array):
        return (256 - (sum(byte_array) % 256)) % 256

    def send_cmd(self, cmd_id, payload=b''):
        frame = bytearray([self.START, cmd_id, len(payload)]) + payload
        frame.append(self.checksum(frame[1:]))
        self.ser.write(frame)

    def read_response(self):
        head = self.ser.read(1)
        if head != b'\x7E':
            return None
        cmd = self.ser.read(1)
        length = self.ser.read(1)[0]
        data = self.ser.read(length)
        _checksum = self.ser.read(1)
        return data

    def start_measurement(self):
        self.send_cmd(0x00, b'\x01\x03')  # mass concentration mode

    def read(self):
        self.send_cmd(0x03)
        data = self.read_response()
        if not data or len(data) != 60:
            return None

        vals = struct.unpack(">ffffffffff", data[0:40])

        return {
            "pm1_0": vals[0],
            "pm2_5": vals[1],
            "pm4_0": vals[2],
            "pm10": vals[3],
            "nc0_5": vals[4],
            "nc1_0": vals[5],
            "nc2_5": vals[6],
            "nc4_0": vals[7],
            "nc10": vals[8],
            "avg_size": vals[9]
        }


###############################################
#  MAIN SCRIPT — LOGS ALL 3 SENSORS
###############################################
def main():
    pt1 = Plantower("/dev/ttyAMA0")  # Plantower #1 on UART0
    pt2 = Plantower("/dev/ttyAMA1")  # Plantower #2 on UART1
    sps = SPS30_UART("/dev/ttyAMA5") # SPS30 on UART5 (ID_SD/ID_SC)

    with open("sensor_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
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
            "sps_nc4_0", "sps_nc10", "sps_size"
        ])

        while True:
            ts = datetime.now().isoformat()

            d1 = pt1.read_frame()
            d2 = pt2.read_frame()
            d3 = sps.read()

            if d1 and d2 and d3:
                row = [
                    ts,

                    # PT1
                    d1["pm1_0"], d1["pm2_5"], d1["pm10"],
                    d1["gt0_3"], d1["gt0_5"], d1["gt1_0"],
                    d1["gt2_5"], d1["gt5_0"], d1["gt10"],
                    d1["temp_C"], d1["rh"], d1["hcho"],

                    # PT2
                    d2["pm1_0"], d2["pm2_5"], d2["pm10"],
                    d2["gt0_3"], d2["gt0_5"], d2["gt1_0"],
                    d2["gt2_5"], d2["gt5_0"], d2["gt10"],
                    d2["temp_C"], d2["rh"], d2["hcho"],

                    # SPS30
                    d3["pm1_0"], d3["pm2_5"], d3["pm4_0"], d3["pm10"],
                    d3["nc0_5"], d3["nc1_0"], d3["nc2_5"],
                    d3["nc4_0"], d3["nc10"], d3["avg_size"]
                ]

                writer.writerow(row)
                print("Logged:", row[0])

            time.sleep(1)


if __name__ == "__main__":
    main()
