#!/usr/bin/env python3
##### code for 2 plantower sensors and 1 sps30, all communicating through UART.
import serial
import time
import csv
import struct
from datetime import datetime

# ============================================================
#                   Plantower PMSx003 Class
# ============================================================

class PlantowerUART:
    def __init__(self, port, name):
        self.port = port
        self.name = name
        self.ser = None
        self.connect()

    def connect(self):
        while True:
            try:
                self.ser = serial.Serial(
                    port=self.port,
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=2
                )
                print(f"[OK] Connected to {self.name} on {self.port}")
                return
            except:
                print(f"[ERROR] Could not open {self.port}, retrying...")
                time.sleep(1)

    def read_frame(self):
        """Read a 40-byte PMS5003/ST frame"""
        try:
            # Look for 0x42 0x4D header
            b1 = self.ser.read(1)
            if b1 != b'\x42':
                return None

            b2 = self.ser.read(1)
            if b2 != b'\x4D':
                return None

            frame = b1 + b2 + self.ser.read(38)
            if len(frame) != 40:
                return None

            # checksum
            data_sum = sum(frame[0:38])
            checksum = frame[38] * 256 + frame[39]
            if data_sum != checksum:
                return None

            return frame

        except:
            self.connect()
            return None

    def parse(self, frame):
        """Return a dict of parsed PMS values"""
        if frame is None:
            return None

        data = {}
        data["pm1"] = frame[10] * 256 + frame[11]
        data["pm25"] = frame[12] * 256 + frame[13]
        data["pm10"] = frame[14] * 256 + frame[15]

        data["gt03"] = frame[16] * 256 + frame[17]
        data["gt05"] = frame[18] * 256 + frame[19]
        data["gt1"]  = frame[20] * 256 + frame[21]
        data["gt25"] = frame[22] * 256 + frame[23]
        data["gt5"]  = frame[24] * 256 + frame[25]
        data["gt10"] = frame[26] * 256 + frame[27]

        # PMS5003ST temperature & RH
        unpacked = struct.unpack(">20h", frame)
        temp_c = unpacked[15] / 10
        data["temp_c"] = temp_c
        data["rh"] = (frame[32] * 256 + frame[33]) / 10

        # Formaldehyde
        data["formaldehyde"] = (frame[28] * 256 + frame[29]) / 1000

        return data


# ============================================================
#                   SPS30 UART Class
# ============================================================

class SPS30_UART:
    """
    SPS30 UART mode sends 60-byte binary packets continuously at 115200 baud.
    We parse them according to Sensirion format.
    """

    FRAME_LENGTH = 60

    def __init__(self, port):
        self.port = port
        self.ser = None
        self.connect()

    def connect(self):
        while True:
            try:
                self.ser = serial.Serial(
                    port=self.port,
                    baudrate=115200,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=2
                )
                print(f"[OK] Connected to SPS30 on {self.port}")
                return
            except:
                print("[ERROR] Could not open SPS30 serial port, retrying...")
                time.sleep(1)

    def read_frame(self):
        """SPS30 UART mode: look for 0x7E header, then read fixed-length frame"""
        try:
            b = self.ser.read(1)
            if b != b'\x7E':   # start byte
                return None

            frame = b + self.ser.read(self.FRAME_LENGTH - 1)
            if len(frame) != self.FRAME_LENGTH:
                return None

            return frame
        except:
            self.connect()
            return None

    def parse(self, frame):
        """Parse SPS30 frame to readable values"""
        if frame is None:
            return None

        # Payload starts after 1 byte header + 1 byte frame length + 1 byte command
        # Sensirion format uses big-endian floats.
        try:
            # Extract 10 float32 values
            payload = frame[3:3 + 10*4]
            values = struct.unpack(">10f", payload)

            return {
                "pm1": values[0],
                "pm25": values[1],
                "pm4": values[2],
                "pm10": values[3],
                "nc05": values[4],
                "nc1": values[5],
                "nc25": values[6],
                "nc4": values[7],
                "nc10": values[8],
                "typ_size": values[9]
            }

        except:
            return None


# ============================================================
#                   Main Logging Loop
# ============================================================

def main():

    # UART device paths
    p1 = PlantowerUART("/dev/ttyAMA0", "Plantower #1")
    p2 = PlantowerUART("/dev/ttyAMA4", "Plantower #2")
    sps = SPS30_UART("/dev/ttyAMA1")

    # Output CSV
    out = open("sensor_log.csv", "w", newline="")
    writer = csv.writer(out)

    # Header row
    writer.writerow([
        "timestamp",

        # Plantower 1
        "p1_pm1", "p1_pm25", "p1_pm10",
        "p1_gt03", "p1_gt05", "p1_gt1", "p1_gt25", "p1_gt5", "p1_gt10",
        "p1_temp_c", "p1_rh", "p1_formaldehyde",

        # Plantower 2
        "p2_pm1", "p2_pm25", "p2_pm10",
        "p2_gt03", "p2_gt05", "p2_gt1", "p2_gt25", "p2_gt5", "p2_gt10",
        "p2_temp_c", "p2_rh", "p2_formaldehyde",

        # SPS30
        "s_pm1", "s_pm25", "s_pm4", "s_pm10",
        "s_nc05", "s_nc1", "s_nc25", "s_nc4", "s_nc10", "s_typ_sz"
    ])

    print("\n[LOGGING] Starting 1-second unified logging...\n")

    while True:
        ts = datetime.utcnow().isoformat()

        # ------- Plantower 1 -------
        f1 = p1.read_frame()
        d1 = p1.parse(f1) if f1 else None

        # ------- Plantower 2 -------
        f2 = p2.read_frame()
        d2 = p2.parse(f2) if f2 else None

        # ------- SPS30 -------
        f3 = sps.read_frame()
        d3 = sps.parse(f3) if f3 else None

        # Write row
        writer.writerow([
            ts,

            # ------- Plantower 1 -------
            *( [
                d1["pm1"], d1["pm25"], d1["pm10"],
                d1["gt03"], d1["gt05"], d1["gt1"],
                d1["gt25"], d1["gt5"], d1["gt10"],
                d1["temp_c"], d1["rh"], d1["formaldehyde"]
              ] if d1 else [None]*12 ),

            # ------- Plantower 2 -------
            *( [
                d2["pm1"], d2["pm25"], d2["pm10"],
                d2["gt03"], d2["gt05"], d2["gt1"],
                d2["gt25"], d2["gt5"], d2["gt10"],
                d2["temp_c"], d2["rh"], d2["formaldehyde"]
              ] if d2 else [None]*12 ),

            # ------- SPS30 -------
            *( [
                d3["pm1"], d3["pm25"], d3["pm4"], d3["pm10"],
                d3["nc05"], d3["nc1"], d3["nc25"],
                d3["nc4"], d3["nc10"], d3["typ_size"]
              ] if d3 else [None]*10 )
        ])

        out.flush()
        time.sleep(1)


if __name__ == "__main__":
    main()
