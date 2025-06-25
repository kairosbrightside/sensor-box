#shutdown script
#needed to alert OP at shutdown

#libraries
import subprocess, os
import time
import RPi.GPIO as GPIO 

import CheckOperationVersion1v3 as CheckOP


#(0) Init
#setup GPIO pins
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
  
#alert OP that the command was recieved
CheckOP.AlertOPpause(1)

time.sleep(2)

#now - alert OP of shutdown 
CheckOP.AlertOPpause(5)

#do shutdown
ERRtrap = subprocess.run(['sudo', 'shutdown', 'now'], stderr=subprocess.PIPE)
