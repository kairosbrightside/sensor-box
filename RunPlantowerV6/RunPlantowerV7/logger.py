#!/usr/bin/env python3
import time
import csv
import struct
import serial
import os
from datetime import datetime
import statistics

from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection, ShdlcDevice
from sensirion_shdlc_driver.command import ShdlcCommand

# =========================
# CONFIG
# =========================
PT1_PORT = "/dev/ttyAMA4"
PT2_PORT = "/dev/ttyAMA1"
SPS_PORT = "/dev/ttyAMA0"

ZERO_FILE = "/media/particulatepi/data/PMoutputData/ZeroCall.txt"
HEATER_FILE = "/media/particulatepi/data/PMoutputData/HeaterRelay.txt"

LOG_FILE = "particle_log.csv"

SAMPLE_RATE = 2  # seconds


# =========================
# FILE STATE HELPERS
# =========================
def read_state(file_path):
    try:
        with open(file_path, "r") as f:
            return f.read().strip() == "[1]"
    except:
        return False


# =========================
# PLANTOWER
# =========================
class Plantower:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600, timeout=2)

    def read(self):
        while True:
            b1 = self.ser.read(1)
            if not b1:
                return None
            if b1 == b'\x42':
                if self.ser.read(1) == b'\x4D':
                    frame = b1 + b'\x4D' + self.ser.read(38)
                    if len(frame) != 40:
                        return None

                    checksum = sum(frame[0:38]) & 0xFFFF
                    recvd = (frame[38] << 8) + frame[39]
                    if checksum != recvd:
                        return None

                    temp = struct.unpack(">h", frame[30:32])[0] / 10.0
                    rh = struct.unpack(">h", frame[32:34])[0] / 10.0

                    return {
                        "pm2_5": frame[12]*256 + frame[13],
                        "temp": temp,
                        "rh": rh
                    }


# =========================
# SPS30 (SHDLC)
# =========================
class SPS30:
    def __init__(self, port):
        sp = ShdlcSerialPort(port=port, baudrate=115200)
        self.dev = ShdlcDevice(ShdlcConnection(sp), slave_address=0)

        # stop (ignore errors)
        try:
            self.dev.execute(ShdlcCommand(0x01, b"", max_response_time=1))
        except:
            pass

        # start (ignore error 67)
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
            return {"pm2_5": vals[1]}
        except:
            return None


# =========================
# MAIN LOGGER
# =========================
def main():

    pt1 = Plantower(PT1_PORT)
    pt2 = Plantower(PT2_PORT)
    sps = SPS30(SPS_PORT)

    pt1_buf, pt2_buf, sps_buf = [], [], []

    zero_offsets = {"pt1": 0, "pt2": 0, "sps": 0}

    last_minute = datetime.now().minute

    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "timestamp",
            "pt1_pm2_5", "pt2_pm2_5", "sps_pm2_5",
            "pt1_temp", "pt1_rh",
            "pt2_temp", "pt2_rh",
            "zero_active", "heater_on"
        ])

        while True:

            zero_active = read_state(ZERO_FILE)
            heater_on = read_state(HEATER_FILE)

            d1 = pt1.read()
            d2 = pt2.read()
            d3 = sps.read()

            if d1: pt1_buf.append(d1["pm2_5"])
            if d2: pt2_buf.append(d2["pm2_5"])
            if d3: sps_buf.append(d3["pm2_5"])

            now = datetime.now()

            if now.minute != last_minute:

                def process(buf, key):
                    if not buf:
                        return None

                    avg = statistics.mean(buf)

                    if zero_active:
                        zero_offsets[key] = avg
                        return 0

                    return avg - zero_offsets[key]

                row = [
                    now.isoformat(timespec="seconds"),

                    process(pt1_buf, "pt1"),
                    process(pt2_buf, "pt2"),
                    process(sps_buf, "sps"),

                    d1["temp"] if d1 else None,
                    d1["rh"] if d1 else None,
                    d2["temp"] if d2 else None,
                    d2["rh"] if d2 else None,

                    int(zero_active),
                    int(heater_on)
                ]

                writer.writerow(row)
                f.flush()

                pt1_buf.clear()
                pt2_buf.clear()
                sps_buf.clear()

                last_minute = now.minute

                print(f"[{row[0]}] Logged minute average")

            time.sleep(SAMPLE_RATE)


if __name__ == "__main__":
    main()
