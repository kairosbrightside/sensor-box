#button

#get libraries
import RPi.GPIO as GPIO
import time
import subprocess

#Here is a script to do checks on the RPi
File4Check = '/home/pi/Desktop/RunPlantower/StartUpWatchDogVersion1v3.py'

#shutdown function
def AlertOPcontinue(nROLLS):
    for i in range(nROLLS):
        time.sleep(0.1)
        GPIO.output(21, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(21, GPIO.LOW)
        
#setup board
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

CheckAction = True
ButtonCnt = 0

while (CheckAction == True):
    
    inState = GPIO.input(4)
    
    if(inState == True):
        ButtonCnt = 0
    else:
        ButtonCnt += 1
    
    #click at 1 second intervals
    time.sleep(1)
    
    #short button push should check if running OK
    if(ButtonCnt >= 1 & ButtonCnt < 5 ):
        
        #will run File4Check from above
        exec(open(File4Check).read())
     
    #long button push should force a shutdown
    if(ButtonCnt >= 1 & ButtonCnt < 5 ):
        
        #force shutdown
        AlertOPpause(5)
        subprocess.run(['shutdown', 'now'])

    
    