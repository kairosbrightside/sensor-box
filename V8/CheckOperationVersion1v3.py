#collection of functions to check
#if the sensor box is working
#this script includes a check for the button programs; builds that do not include a UPS

# CheckOperationVersion (Pi 5 + safe GPIO architecture)

import subprocess
import os
import datetime
import time

# =========================
# CONFIG
# =========================
ALERT_FILE = "/tmp/sensor_alert.txt"


# =========================
# (1) INTERNET CHECK
# =========================
def CheckInternet(ip2ping):
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '1', ip2ping],
            stdout=subprocess.PIPE
        )
        output = result.stdout.decode()

        if "0% packet loss" in output:
            return 0.0
        else:
            return 1.0

    except:
        return 1.0


# =========================
# (2) DATA FRESHNESS CHECK
# =========================
def IsLateMeasurement(root, FleInDir, LateInMinutes):

    nUpdatedFiles = 0
    now = datetime.datetime.now()
    threshold = now - datetime.timedelta(minutes=LateInMinutes)

    for item in FleInDir:
        if '1Min.txt' in item:
            try:
                path = os.path.join(root, item)

                with open(path) as f:
                    last_line = f.readlines()[-1]

                parts = last_line.split(',')

                MeasurementTime = datetime.datetime(
                    year=int(parts[0]),
                    month=int(parts[1]),
                    day=int(parts[2]),
                    hour=int(parts[3]),
                    minute=int(parts[4])
                )

                if MeasurementTime > threshold:
                    nUpdatedFiles += 1

            except:
                pass

    return nUpdatedFiles


# =========================
# (3) RESTART SCRIPTS
# =========================
def RestartRunPMShell(script):

    try:
        ps = subprocess.check_output(['ps', '-ef']).decode()

        for line in ps.splitlines():
            if 'python3' in line and 'WatchDog' not in line and 'CheckInternet' not in line:
                try:
                    pid = int(line.split()[1])
                    subprocess.run(['kill', str(pid)])
                except:
                    pass

        subprocess.Popen([script])

    except Exception as e:
        print("Restart error:", e)


# =========================
# (4) ALERT SYSTEM (FILE-BASED)
# =========================
def _write_alert(msg):
    try:
        with open(ALERT_FILE, "w") as f:
            f.write(msg)
    except:
        pass


def AlertOPpause(nROLLS):
    # Example: "pause:5"
    _write_alert(f"pause:{nROLLS}")


def AlertOPcontinue(nROLLS):
    # Example: "continue:20"
    _write_alert(f"continue:{nROLLS}")