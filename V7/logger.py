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
from config import (
    DATA_DIR,
    CONTROL_DIR,
    SITE,
    PT1_PORT,
    PT2_PORT,
    SPS_PORT,
)

ZERO_FILE = CONTROL_DIR / "ZeroCall.txt"
HEATER_FILE = CONTROL_DIR / "HeaterRelay.txt"
CSV_LOG = None

SAMPLE_RATE = 10


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
    ### ADD ZEROING LATER
    pt1 = Plantower(PT1_PORT)
    pt2 = Plantower(PT2_PORT)
    sps = SPS30(SPS_PORT)

    last = {"pt1": None, "pt2": None, "sps": None}
    buffers = {"pt1": [], "pt2": [], "sps": []}
    zero_offsets = {"pt1": 0, "pt2": 0, "sps": 0}

    last_minute = datetime.now().minute
    current_day = datetime.now().strftime("%Y_%m_%d")

    writer = None
    csv_file = None

    while True:

        now = datetime.now()

        # =========================
        # DAILY FILE ROTATION
        # =========================
        new_day = now.strftime("%Y_%m_%d")

        if new_day != current_day or writer is None:

            current_day = new_day

            if csv_file:
                csv_file.close()

            filename = f"{SITE}_{current_day}.csv"
            path = os.path.join(DATA_DIR, filename)

            file_exists = os.path.exists(path)

            csv_file = open(path, "a", newline="")
            writer = csv.writer(csv_file)

            # only write header once
            if not file_exists:
                writer.writerow([
                    "timestamp",
                    "pt1_pm2_5",
                    "pt2_pm2_5",
                    "sps_pm2_5",
                    "pt1_temp",
                    "pt1_rh",
                    "pt2_temp",
                    "pt2_rh",
                    "zero",
                    "heater"
                ])

            print(f"Opened daily log: {filename}")

        # =========================
        # READ STATES
        # =========================
        zero = read_state(ZERO_FILE)
        heater = read_state(HEATER_FILE)

        # =========================
        # READ SENSORS
        # =========================
        for name, sensor in [("pt1", pt1), ("pt2", pt2), ("sps", sps)]:
            try:
                data = sensor.read()
            except Exception as e:
                print(f"Error reading {name}: {e}")
                data = None

            if data:
                last[name] = data
                buffers[name].append(data["pm2_5"])

        # =========================
        # PROCESS ONCE PER MINUTE
        # =========================
        if now.minute != last_minute:

            def process(buf, key):

                if not buf:
                    return 999

                avg = statistics.mean(buf)

                # during zeroing:
                # update offset
                if zero:
                    zero_offsets[key] = avg
                    return 0

                return avg - zero_offsets[key]

            pt1_val = process(buffers["pt1"], "pt1")
            pt2_val = process(buffers["pt2"], "pt2")
            sps_val = process(buffers["sps"], "sps")

            # =========================
            # WRITE DAILY CSV
            # =========================
            row = [
                now.isoformat(timespec="seconds"),

                pt1_val,
                pt2_val,
                sps_val,

                last["pt1"]["temp"] if last["pt1"] else 999,
                last["pt1"]["rh"] if last["pt1"] else 999,

                last["pt2"]["temp"] if last["pt2"] else 999,
                last["pt2"]["rh"] if last["pt2"] else 999,

                int(zero),
                int(heater)
            ]

            writer.writerow(row)
            csv_file.flush()

            # =========================
            # WRITE ENVIDAS FILES
            # =========================
            """             if last["pt1"]:
                row1 = format_envidas(now, last["pt1"], zero, SN1)
                write_envidas(SN1, row1)

            if last["pt2"]:
                row2 = format_envidas(now, last["pt2"], zero, SN2)
                write_envidas(SN2, row2) """

            # =========================
            # RESET BUFFERS
            # =========================
            for b in buffers.values():
                b.clear()

            last_minute = now.minute

            print(f"[{now}] Logged minute average")

        time.sleep(SAMPLE_RATE)


if __name__ == "__main__":
    main()