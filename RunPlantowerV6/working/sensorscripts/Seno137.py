#This gets data from the DFROBOT seno137 temperature and rh
#DHT Temperature and humidty sensor

#assumes sensor signal wire is tied to GPIO pin 4

######################################### 
#(1) import library
######################################### 
import os, sys
import shutil
import datetime, time

import Adafruit_DHT

import numpy as np
import pandas as pd

import logging

#sensor setup
sensorType = 'SENO137'
sn = '0'
site = "LabTEST"
DataOutDirectory = "/mnt/sd1/PMoutputData/" #output directory
SampleRate = 10 #sec - pause n seconds between measurements

if (sensorType == 'SENO137'):
    sensor = Adafruit_DHT.DHT22
    pin = 4

######################################### 
#(2) create log
######################################### 
fleLog = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "Log.txt")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s:%(levelname)s:%(levelno)s:%(message)s')

file_handler = logging.FileHandler(fleLog)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

######################################### 
#(3) functions
#########################################

def SetupDataFile(fleOut, writetype):
    
    if os.path.exists(fleOut) == True:
        logger.info('Restarting Run: Appending data to' + fleOut) 
    else:
        try:
            file2write = open(fleOut, writetype) 
        except Exception as e:
            logger.info('Setup file Error')
        else:
            file2write.close()
            
        OKfilePermission = (os.access(fleOut, os.R_OK)) & (os.access(fleOut, os.W_OK)) #read-write privaleges?
        if (OKfilePermission == False):
            logger.info('File Permission Error: ' + fleOut + ' Exiting!') 
            sys.exit(1) #exit

#aggregation
def Aggregate2Send(DataIn, METheader4Aggregate):

    #initiate data frame for aggregated data
    minute2send = pd.DataFrame(-99, index=range(0,1),columns=METheader4Aggregate)

    #flag for aggregate
    aggregateAVG = pd.DataFrame(DataIn.mean()).transpose()
    aggregateAVG.round(0).astype(int)

    aggregateMID = pd.DataFrame(DataIn.median()).transpose()
    aggregateMID.round(0).astype(int)

    #now insert the statistics into the minute2send
    minute2send.loc[0,'year'] = aggregateMID.loc[0,'year'] # time
    minute2send.loc[0,'month'] = aggregateMID.loc[0,'month']
    minute2send.loc[0,'day'] = aggregateMID.loc[0,'day']
    minute2send.loc[0,'hour'] = aggregateMID.loc[0,'hour']
    minute2send.loc[0,'minute'] = aggregateMID.loc[0,'minute']
    
    minute2send.loc[0,'AmbientTemperature'] = aggregateAVG.loc[0,'Temperature'] #avg temp
    minute2send.loc[0,'AmbientRelativeHumidity'] = aggregateAVG.loc[0,'RelativeHumidity'] #avg rh

    return(minute2send)


#######d##################################
#(4) setup header & modbus data storage
#########################################
#raw
fleHeader = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "DataHeader.txt")
    
METheader = ["year", "month", "day", "hour", "minute", "second",
            "Temperature", "RelativeHumidity"]

HeaderLine = ",".join(METheader) + "\n"

with open(fleHeader, "a") as myfile:
    myfile.write(HeaderLine)

#aggregated
fleHeader = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "AggregateDataHeader.txt")
    
METheader4Aggregate = ["year", "month", "day", "hour", "minute", 
                        "AmbientTemperature", "AmbientRelativeHumidity"]

HeaderLine = ",".join(METheader4Aggregate) + "\n"

with open(fleHeader, "a") as myfile:
    myfile.write(HeaderLine)
    
########################################
## (5) On RPi storage - daily records
#########################################
DateStr4Out = str(datetime.datetime.now().day) + '_' + str(datetime.datetime.now().month) + '_' + str(datetime.datetime.now().year)
        
fleoutFSTDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1sec" + DateStr4Out + ".txt")
SetupDataFile(fleoutFSTDaily, "a")       
        
fleoutAVGDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min" + DateStr4Out + ".txt")
SetupDataFile(fleoutAVGDaily, "a")

fleoutAVG = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min" + ".txt")
SetupDataFile(fleoutAVG, "a")
########################################
# (6) Read serial data from plantower
########################################
#Initialize 
iter = 0

MeasureTime = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
Day_previous = MeasureTime.day
minute_past  = MeasureTime.minute

#Initiate a dataframe for the incoming data
DataIn = pd.DataFrame(np.nan, index=range(0,1),columns=METheader)

IndRow = 0
 
while True:
    try:
        #sets sampling rate
        time.sleep(SampleRate) 

        #time - should not observe daylight savings
        MeasureTime = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
        
        try:
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
            temperature  = temperature * 10 # met block
            humidity  = humidity * 10
        except:
            logger.info('SENO137 read error.  insert -9')
            humidity = int(-99)
            temperature = int(-99)
            
        #check plausibility
        #Parse rcv serial string to DataIn: see PMS5003st manual for var. assignments
        DataIn.ix[IndRow,0]  = int(MeasureTime.year)        #time block
        DataIn.ix[IndRow,1]  = int(MeasureTime.month)
        DataIn.ix[IndRow,2]  = int(MeasureTime.day)
        DataIn.ix[IndRow,3]  = int(MeasureTime.hour)
        DataIn.ix[IndRow,4]  = int(MeasureTime.minute)
        DataIn.ix[IndRow,5]  = int(MeasureTime.second)
        
        # met block
        DataIn.ix[IndRow,6]  = temperature
        DataIn.ix[IndRow,7]  = humidity
        
        #add a row
        IndRow += 1
        
        ############################################################
        #1 min. interval
        ############################################################
        #save data to disk
        minute_current = MeasureTime.minute
        
        if (minute_current != minute_past):
            
            #Reset the minute for record keeping
            minute_past = minute_current
            
            #do the ENVIDAS aggregation
            minute2send = Aggregate2Send(DataIn, METheader4Aggregate)
            
            try:
                with open(fleoutAVG, 'w') as myfile:
                    minute2send.to_csv(myfile, header=False, index=False, float_format='%.0f')
            except:
                logger.info("Error: Did not write data to server")
                
            ####### RPi Backup logs #########################   
            #save if there is free space
            total, used, free = shutil.disk_usage(DataOutDirectory)
            
            fracFree = free/total
            
            if (fracFree >= 0.3):
                #fast data
                try:
                    with open(fleoutFSTDaily, "a") as myfile:
                        DataIn.to_csv(myfile, header=False, index=False)
                except:
                    logger.info("Fast file write error")
                    
                #minute data
                try:
                    with open(fleoutAVGDaily, "a") as myfile:
                        minute2send.to_csv(myfile, header=False, index=False, float_format='%.0f')
                except:
                    logger.info("Slow file write error")
                    
            else:
                logger.info("Low disk space. Stopped logging data to local site")

            #Reset DataIn for incoming data
            IndRow = 0
            DataIn = pd.DataFrame(np.nan, index=range(0,1),columns=METheader)
        
        
        ############################################################
        #Every Day
        ############################################################
        #make a new file for data output
        Day_current = MeasureTime.day
        
        if (Day_current != Day_previous):
            
            DateStr4Out = str(Day_current) + '_' + str(MeasureTime.month) + '_' + str(MeasureTime.year)

            fleoutFSTDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1sec" + DateStr4Out + ".txt")
            SetupDataFile(fleoutFSTDaily, "a")       
            
            fleoutAVGDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min" + DateStr4Out + ".txt")
            SetupDataFile(fleoutAVGDaily, "a",)

            Day_previous = Day_current
            
    except Exception as e:
        
        logger.info("!!Crashed!! " + str(e))
        logger.info("SENO137 exiting.") 
        
        sys.exit(1) # exit the program