#!/bin/bash
sudo chmod 774 /home/piray/sensor-box/V8/*.py
# move into script directory
cd /home/piray/sensor-box/V8

python3 logger.py &
python3 hardware_control.py &


python3 rpm_counter.py &
python3 periodic_restart.py &
python3 watchdog.py &


python3 button_control.py &