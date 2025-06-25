# controlling the GPIO pins for calibrations

#---------------------------------------------------------------------------# 
# library for controling GPIO pins on RPi
#---------------------------------------------------------------------------#
import datetime, time
import RPi.GPIO as GPIO
#---------------------------------------------------------------------------#

GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.OUT)

#---------------------------------------------------------------------------#
##check Cal call every minute
PowerCycleCNT = 0

while True:
    
    time.sleep(2) 
    
    GPIO.output(13, GPIO.HIGH)

    time.sleep(2)
    
    GPIO.output(13, GPIO.LOW)
    
    time.sleep(0.5) 
    
    PowerCycleCNT+=1
    
    GPIO.output(13, GPIO.HIGH)

    time.sleep(0.5)
    
    GPIO.output(13, GPIO.LOW)
    
    time.sleep(0.5) 
    
    GPIO.output(13, GPIO.HIGH)

    time.sleep(0.5)
    
    PowerCycleCNT+=1
    
    GPIO.output(13, GPIO.LOW)
    
    time.sleep(10) 
    
    GPIO.output(13, GPIO.HIGH)

    time.sleep(10)
    
    GPIO.output(13, GPIO.LOW)
    
    PowerCycleCNT+=1
    
    print(PowerCycleCNT)
    
            

