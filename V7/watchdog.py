import subprocess
import time
import os

from config import DATA_DIR, SERVICE_NAME
# =========================
# CONFIG
# =========================

REQUIRED_PROCESSES = [
    "logger.py",
    "hardware_control.py",
    "rpm_counter.py",
    "periodic_restart.py",
]


RESTART_COOLDOWN = 300   # seconds


# =========================
# PROCESS CHECK
# =========================

def processes_running():

    try:
        ps = subprocess.check_output(['ps', '-ef']).decode()

        missing = []

        for proc in REQUIRED_PROCESSES:
            if proc not in ps:
                missing.append(proc)

        if missing:
            print("Missing processes:", missing)
            return False

        return True

    except Exception as e:
        print("Process check failed:", e)
        return False


# =========================
# DATA CHECK
# =========================

def data_updating(data_dir, max_age=120):

    try:

        today = time.strftime("%Y_%m_%d")
        filename = f"PSU_{today}.csv"

        path = os.path.join(data_dir, filename)

        age = time.time() - os.path.getmtime(path)

        if age > max_age:
            print(f"Data file stale: {age:.1f} sec old")
            return False

        return True

    except Exception as e:
        print("Data check failed:", e)
        return False


# =========================
# RESTART
# =========================

last_restart = 0

def restart_service(reason):

    global last_restart

    now = time.time()

    # prevent restart loops
    if now - last_restart < RESTART_COOLDOWN:
        print("Restart suppressed (cooldown)")
        return

    last_restart = now

    print(f"Restarting service: {reason}")

    try:
        subprocess.run([
            'sudo',
            'systemctl',
            'restart',
            SERVICE_NAME
        ])

    except Exception as e:
        print("Restart failed:", e)


### main

while True:

    if not processes_running():
        restart_service("missing process")

    elif not data_updating(DATA_DIR):
        restart_service("stale data")

    time.sleep(60)