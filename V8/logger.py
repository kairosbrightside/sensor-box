import time
import csv
import os
from datetime import datetime
import statistics

from sensors.plantower import Plantower
from sensors.sps30 import SPS30

# =========================
# CONFIG
# =========================
PT1_PORT = "/dev/ttyAMA1"
PT2_PORT = "/dev/ttyAMA4"
SPS_PORT = "/dev/ttyAMA0"

SITE = "PSU"
SN1 = "1"
SN2 = "2"

DATA_DIR = "/media/particulatepi/data/PMoutputData/"
CSV_LOG = "particle_log.csv"

ZERO_FILE = DATA_DIR + "ZeroCall.txt"
HEATER_FILE = DATA_DIR + "HeaterRelay.txt"

SAMPLE_RATE = 2


# =========================
# HELPERS
# =========================
def read_state(path):
    try:
        with open(path) as f:
            return f.read().strip() == "[1]"
    except:
        return False


def write_envidas(sn, row):
    """
    Write ENVIDAS-compatible file (overwrite)
    """
    filename = f"{SITE}_PMS5003st_sn{sn}_1Min.txt"
    path = os.path.join(DATA_DIR, filename)

    with open(path, "w") as f:
        f.write(",".join(map(str, row)) + "\n")


def format_envidas(dt, data, zero, sn):
    """
    Create DEQ-compatible row
    NOTE: simplified but compatible structure
    """

    return [
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, dt.second,

        # APM (approx same as PM for now)
        data["pm1"], data["pm2_5"], data["pm10"],

        # PM
        data["pm1"], data["pm2_5"], data["pm10"],

        # particle counts (not available → dummy)
        999, 999, 999, 999, 999, 999,

        # formaldehyde (not used)
        0,

        # temperature (Kelvin ×10)
        int((data["temp"] + 273.15) * 10) if data["temp"] else 0,

        # RH ×10
        int(data["rh"] * 10) if data["rh"] else 0,

        int(zero),

        4,      # code_version
        int(sn)
    ]


# =========================
# MAIN
# =========================
def main():

    pt1 = Plantower(PT1_PORT)
    pt2 = Plantower(PT2_PORT)
    sps = SPS30(SPS_PORT)

    last = {"pt1": None, "pt2": None, "sps": None}
    buffers = {"pt1": [], "pt2": [], "sps": []}
    zero_offsets = {"pt1": 0, "pt2": 0, "sps": 0}

    last_minute = datetime.now().minute

    # Combined CSV (your data)
    with open(CSV_LOG, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "pt1_pm2_5", "pt2_pm2_5", "sps_pm2_5",
            "pt1_temp", "pt1_rh",
            "pt2_temp", "pt2_rh",
            "zero", "heater"
        ])

        while True:

            zero = read_state(ZERO_FILE)
            heater = read_state(HEATER_FILE)

            # Read sensors
            for name, sensor in [("pt1", pt1), ("pt2", pt2), ("sps", sps)]:
                data = sensor.read()
                if data:
                    last[name] = data
                    buffers[name].append(data["pm2_5"])

            now = datetime.now()

            # Every minute → process
            if now.minute != last_minute:

                def process(buf, key):
                    if not buf:
                        return None
                    avg = statistics.mean(buf)

                    if zero:
                        zero_offsets[key] = avg
                        return 0
                    return avg - zero_offsets[key]

                pt1_val = process(buffers["pt1"], "pt1")
                pt2_val = process(buffers["pt2"], "pt2")
                sps_val = process(buffers["sps"], "sps")

                # =========================
                # WRITE YOUR CSV
                # =========================
                row = [
                    now.isoformat(timespec="seconds"),
                    pt1_val, pt2_val, sps_val,

                    last["pt1"]["temp"] if last["pt1"] else None,
                    last["pt1"]["rh"] if last["pt1"] else None,

                    last["pt2"]["temp"] if last["pt2"] else None,
                    last["pt2"]["rh"] if last["pt2"] else None,

                    int(zero),
                    int(heater)
                ]

                writer.writerow(row)
                f.flush()

                # =========================
                # WRITE ENVIDAS FILES
                # =========================
                if last["pt1"]:
                    row1 = format_envidas(now, last["pt1"], zero, SN1)
                    write_envidas(SN1, row1)

                if last["pt2"]:
                    row2 = format_envidas(now, last["pt2"], zero, SN2)
                    write_envidas(SN2, row2)

                # reset buffers
                for b in buffers.values():
                    b.clear()

                last_minute = now.minute
                print("Logged minute data")

            time.sleep(SAMPLE_RATE)


if __name__ == "__main__":
    main()