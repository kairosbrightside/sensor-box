#!/usr/bin/env python3
import subprocess
import time
import os
from datetime import datetime

LOG_FILE = "sensor_log.csv"
CHECK_INTERVAL = 60  # seconds

def is_process_running(name):
    try:
        output = subprocess.check_output(["ps", "-ef"]).decode()
        return name in output
    except:
        return False


def restart_service():
    print("Restarting sensor service...")
    subprocess.run(["sudo", "systemctl", "restart", "sensor-box.service"])


def data_is_fresh(file_path, max_age_sec=180):
    try:
        mtime = os.path.getmtime(file_path)
        age = time.time() - mtime
        return age < max_age_sec
    except:
        return False


def main():
    print("Watchdog started")

    while True:
        print(f"\n[{datetime.now()}] Running checks...")

        logger_ok = is_process_running("logger.py")
        heater_ok = is_process_running("HeaterControl.py")
        data_ok = data_is_fresh(LOG_FILE)

        print(f"Logger running: {logger_ok}")
        print(f"Heater running: {heater_ok}")
        print(f"Data fresh: {data_ok}")

        if logger_ok and heater_ok and data_ok:
            print("System OK")
        else:
            print("System issue detected → restarting")
            restart_service()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
