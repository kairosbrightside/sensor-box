# controlling the GPIO pins for calibrations

#---------------------------------------------------------------------------# 
# library for controling GPIO pins on RPi
#---------------------------------------------------------------------------#
import sys, os
import datetime, time
import RPi.GPIO as GPIO
import statistics

import logging
#---------------------------------------------------------------------------#
#inputs from shell
#---------------------------------------------------------------------------#
#stable ==> here
DataOutDirectory = "/media/pi/data/PMoutputData/" #output directory
sensorType = "PMS5003st"

#inputs from shell
#site = str(sys.argv[1])
#sn = str(sys.argv[2])
site = 'BOX'
sn = '1'
SensorData = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min.txt")

######################################### 
#(2) create log
#########################################
HeaterLog = (DataOutDirectory + "Heater_" + "Log.txt")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s:%(levelname)s:%(levelno)s:%(message)s')

file_handler = logging.FileHandler(HeaterLog)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

#---------------------------------------------------------------------------#
#set up GPIO ports
try:
    pinhigh = GPIO.input(13)
except:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(13, GPIO.OUT)

#see if pin works
try:
    GPIO.output(13, GPIO.LOW)
    pinhigh = GPIO.input(13)
    logger.info('Heater pin works.  Force heater off.')
    
except:
    logger.info('Heater pin error.')
    pinhigh = 0

#---------------------------------------------------------------------------#
# init RH
RH_i = 50
RH_iminus1 = 50
RH_iminus2 = 50
RH_iminus3 = 50
RH_iminus4 = 50

#---------------------------------------------------------------------------#

##check Cal call every minute
while True:
    
    time.sleep(60) 
    
    ifile = SensorData
    
    try:
        with open(ifile, "r") as myfile:
            PtowerDATA = myfile.readlines()[-1] #-1 = last line         
    except: 
        logger.info('No PtowerData to inform heater')
    
    RH_i = PtowerDATA.split(',')[10] #RH * 10
    RH_i = int(RH_i)/10 #convert to percent units
    # print(RH_i)
    
    # get 5 min RH average 
    RH_iminus1 = RH_i
    RH_iminus2 = RH_iminus1
    RH_iminus3 = RH_iminus2
    RH_iminus4 = RH_iminus3
    RH = statistics.mean([RH_i, RH_iminus1, RH_iminus2, RH_iminus3, RH_iminus4])

    # now set the GPIOpin 
    pinhigh = GPIO.input(13)
    
    if (RH >= 50) & (pinhigh == False):
        GPIO.output(13, GPIO.HIGH)
        #print('pin set high')
        
    if (RH < 30) & (pinhigh == True):
        GPIO.output(13, GPIO.LOW)
        # print('pin set low')

    # if (RH >= RHthreshold) & (pinhigh == False) & (WorkingHeater == True):
    #    GPIO.output(13, GPIO.HIGH)
        
    #    print('pin set high')
        
    # if (RH < RHthreshold) & (pinhigh == True) & (WorkingHeater == True):
    #    GPIO.output(13, GPIO.LOW)
        
    #    print('pin set low')
        
    # force pin low
    # if (pinhigh == 1):       
    #   OnTimer += 1
    #   OnTimer2Minute = (OnTimer * CheckInt)/60
    #   if (OnTimer2Minute >= 30):
    #       #force pin low if it was set to high for 30 min
    #       GPIO.output(13, GPIO.LOW)
    #       OnTimer = 0
    
    #       WorkingHeater = False
           
    #       logger.info('Heater broken: Forced heater off.')
           
    # else:
    #   OnTimer = 0


