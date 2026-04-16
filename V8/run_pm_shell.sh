#!/bin/bash

python3 logger.py &
python3 do_zero.py &
python3 rpm_counter.py &
python3 periodic_restart.py &