#!/bin/bash

############################################################
# RunPlantower V7 Launcher
# Cleaned + simplified DEQ-style runner
############################################################

# ===== CONFIG =====

SITE="PSU"

# Plantower sensors: (SN PORT)
SENSORS=(
  "1 ttyAMA4"
  "2 ttyAMA1"
)

# Paths (adjust if needed)
BASE_DIR="/home/piray/sensor-box/RunPlantowerV6/RunPlantowerV7"

LOGGER="$BASE_DIR/logger.py"
HEATER="$BASE_DIR/HeaterControl.py"
RPM="$BASE_DIR/RPMCounter.py"
BUTTON="$BASE_DIR/ButtonVersion2.py"
WATCHDOG="$BASE_DIR/watchdog.py"

PYTHON="/usr/bin/python3"

############################################################
# ===== SETUP =====
############################################################

echo "========================================"
echo "Starting RunPlantower V7"
echo "Site: $SITE"
echo "Time: $(date)"
echo "========================================"

cd "$BASE_DIR" || exit 1

############################################################
# ===== START PLANTOWER LOGGING (if applicable) =====
############################################################

echo "Starting sensors..."

for entry in "${SENSORS[@]}"; do
    SN=$(echo $entry | awk '{print $1}')
    PORT=$(echo $entry | awk '{print $2}')

    echo "  Sensor SN=$SN on $PORT"

    # If you later split logger per sensor, do it here
    # $PYTHON logger.py "$SITE" "$SN" "$PORT" &

done

############################################################
# ===== START SERVICES =====
############################################################

echo "Starting core services..."

$PYTHON "$LOGGER" >> logger.log 2>&1 &
$PYTHON "$HEATER" >> heater.log 2>&1 &
$PYTHON "$RPM" >> rpm.log 2>&1 &
$PYTHON "$BUTTON" >> button.log 2>&1 &
$PYTHON "$WATCHDOG" >> watchdog.log 2>&1 &

############################################################
# ===== KEEP ALIVE =====
############################################################

echo "All processes started."

# Wait for background jobs
wait