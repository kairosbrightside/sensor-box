#button interface

#get libraries
import RPi.GPIO as GPIO
import time
import subprocess

import CheckOperationVersion1v3 as CheckOP
import StartUpWatchDogVersion1v3 as WatchDog
        
#setup board
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#set 21 if needed
try:
    pinhigh = GPIO.input(21)
except:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.OUT)
    
#init
inState0 =  1
ButtonCnt = 0

while True:
    #get button input
    inState = GPIO.input(4)
    
    if (inState != inState0):
        #if button held down for a short time = run startup diagnostics
        if((ButtonCnt>1) & (ButtonCnt<=5)):
            WatchDog.doWatchDog(0)
        #if button held down for a long time = force shutdown
        if(ButtonCnt > 5): 
            CheckOP.AlertOPpause(5)
            GPIO.cleanup()
            subprocess.run(['sudo','shutdown', 'now'])
        
    if(inState == True):
        ButtonCnt = 0
    else:
        ButtonCnt += 1
    
    #click at 1 second intervals
    inState0 = inState
    time.sleep(1)
    
     