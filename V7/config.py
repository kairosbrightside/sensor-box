from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
CONTROL_DIR = BASE_DIR / "control"
LOG_DIR = BASE_DIR / "logs"

SERVICE_NAME = "sensor-box.service"


SITE = "PSU"

PT1_PORT = "/dev/ttyAMA1"
PT2_PORT = "/dev/ttyAMA4"
SPS_PORT = "/dev/ttyAMA0"

DATA_DIR.mkdir(exist_ok=True)
CONTROL_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)