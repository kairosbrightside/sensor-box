#This script reads data from PMSX003st sensors 
# The script is broken into 6 sections:
##(1) import libraries & inputs for shell
##(2) make a log file
##(3) define functions 
##(5) establish RPi-plantower serial connection 
##(6) read plantower data, aggregate, and write to disk
     
#########################################  
#(1) inputs
##########################################
#libraries
import os, sys
import shutil

import datetime, time
import serial
import RPi.GPIO as GPIO
import numpy as np
#import /usr/lib/python2.7/dist-packages/pandas as pd
import pandas as pd

import logging

##input from shell
#site = sys.argv[1]
#site = str(site)
##
#sn = sys.argv[2]
#sn = str(sn)
##
#Port2Focus = sys.argv[3]
#Port2Focus = str(Port2Focus)

site = "BOX"
sn = "1"
Port2Focus = "serial0"

#adjust here
sensorType = "PMSX003"
#DataOutDirectory = "/data/PMoutputData/" #output directory
DataOutDirectory = "/media/pi/data/PMoutputData/" #output directory
SampleRate = 2 #sec - pause n seconds between measurements

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
#set up sensor configuration
def plantower_serial_connection(_serPort):
    '''Establishes serial connection between RPi and plantower:
    inputs: _serPort = RPi port attached to plantower
    
    returns: ser = serial object for the plantower connection
    ErrorMessage = error message associated with a failed serial connection w/"none" == no errors/connection is OK''' 
    
    ErrorFlag = 'init'
    IsPortOpen = False
    nTrys = 0
    
    while ((IsPortOpen == False) & (nTrys <= 3)):
        
        #make a connection
        try:
            ser = serial.Serial() #serial object
            ser.port = '/dev/' + _serPort  
            ser.baudrate = 9600
            ser.stopbits = serial.STOPBITS_ONE
            ser.parity = serial.PARITY_NONE
            ser.bytesize = serial.EIGHTBITS
            ser.timeout = 5
        except Exception as e:
            nTrys += 1
            logger.info('Could not make a serial object.')
            time.sleep(1)#pause
        else:
            #open and check if it is open
            try:
                ser.open()
            except Exception as e:
                nTrys += 1
                logger.info('Problem Connecting to plantower: ' + str(e))
                time.sleep(1)#pause
            else:
                IsPortOpen = ser.is_open
                ErrorFlag = 'none'
    return(ser, ErrorFlag)


##read in the serial string from the plantower and do basic QA/QC
def read_pm_line(_port):
    '''Reads serial data from plantower
    inputs: _port = serial object from plantower_serial_connection
    
    return:
    rv is the data (serial string) from the plantower
    Elaspsed is how long it took to read the serial string in seconds
    BaseErrorMessage = error message associated with a failed serial read w/ "none" == all OK'''
    
    #initialize
    BufferReadTry = False
    nSearchForStartReads = 0
    
    rv = b''
    Elaspsed = -999
    BaseErrorFlag = 'ErrLevel1'
    
    #do the read
    while ((BufferReadTry == False) & (nSearchForStartReads < 200)):
        try:
            
            nSearchForStartReads += 1
            
            #start of serial read
            t_o = time.time()
            
            #PMS5003st gives a 32 character string
            ch1 = _port.read()
            if ch1 == b'\x42':
                ch2 = _port.read()
                if ch2 == b'\x4d':
                    rv += ch1 + ch2
                    rv += _port.read(30)
                    
                    Elaspsed = time.time() - t_o #when read line is working elaspsed ~= 0.0003 seconds      
                    
                    BaseErrorFlag = 'none'
                    BufferReadTry = True

        #base error
        except Exception as e:
            
            rv = b''
            Elaspsed = -999
            BaseErrorFlag = 'ErrLevel1'
            
    return(rv, Elaspsed, BaseErrorFlag)
            
#error check for incoming serial data          
def read_pm_error_check(rv, Elaspsed, BaseErrorFlag, iter):
    '''Error checking on read_pm_line'''
    
    ErrorMessage = 'none'
    iter += 1
    
    ##n trys 
    ##check if a base error was thrown
    if (BaseErrorFlag != 'none'):
        logger.info('BaseError:' + str(BaseErrorFlag))
        ErrorMessage = 'ErrFlag1'
    ##did not get a read
    if (rv == b''):
        logger.info('EmptyReadLine')
        ErrorMessage = 'ErrFlag1'
    ##read took too long
    if (Elaspsed > 2):
        logger.info('HangingReadlineError')
        ErrorMessage = 'ErrFlag1'
    ##length 
    if (len(rv) != 32):
        logger.info('ReadLineLengthError')
        ErrorMessage = 'ErrFlag1'
    ##check sum 
    if (len(rv) == 32):
        DataSum = sum(rv[0:29])
        cksum = (rv[30] * 256 + rv[31])
        if (DataSum != cksum):
            logger.info('CheckSumFailError')
            ErrorMessage = 'ErrFlag1'
            
    if (iter > 10):
        logger.info('ExceededMaxTry')
        ErrorMessage = 'ErrFlag2'
        
    ##good read
    if (ErrorMessage == 'none'):
        iter = 0 #good read; reset counter
    
    return(rv, ErrorMessage, iter)
    
# File management       
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
#aggregation
def Aggregate2Send(DataIn, ENVIDASheader):

    #initiate data frame for aggregated data
    minute2send = pd.DataFrame(-99, index=range(0,1),columns=ENVIDASheader)

    #flag for aggregate
    DidAggregation = 0
    
    #subset to non-zero observations
    try:
        
        ZeroOff = DataIn['zero'] == 0
        aggregateCNT = pd.DataFrame(DataIn[ZeroOff].count()).transpose()
        
        #all observations
        aggregateCNTall = pd.DataFrame(DataIn.count()).transpose()
        
    except:
        
        logger.info('Error: DataIn count.')           
    
    #subset for non-zero
    if (aggregateCNT.pm2_5[0] >= 3):
        
        DoingZero = 0
        
        aggregateCNT = pd.DataFrame(DataIn[ZeroOff].count()).transpose()
        aggregateCNT.round(0).astype(int)
    
        aggregateAVG = pd.DataFrame(DataIn[ZeroOff].mean()).transpose()
        aggregateAVG.round(0).astype(int)

        aggregateSTD = pd.DataFrame(DataIn[ZeroOff].std()).transpose()
        aggregateSTD.round(0).astype(int)

        aggregateMID = pd.DataFrame(DataIn[ZeroOff].median()).transpose()
        aggregateMID.round(0).astype(int)

        aggregateMIN = pd.DataFrame(DataIn[ZeroOff].min()).transpose()
        aggregateMIN.round(0).astype(int)
        
        aggregateMAX = pd.DataFrame(DataIn[ZeroOff].max()).transpose()
        aggregateMAX.round(0).astype(int)
         
        DidAggregation = 1
        
    else:
        
        if (aggregateCNTall.pm2_5[0] >= 3):
            
            try:
                DoingZero = 1
                
                aggregateCNT = pd.DataFrame(DataIn.count()).transpose()
                aggregateCNT.round(0).astype(int)
            
                aggregateAVG = pd.DataFrame(DataIn.mean()).transpose()
                aggregateAVG.round(0).astype(int)

                aggregateSTD = pd.DataFrame(DataIn.std()).transpose()
                aggregateSTD.round(0).astype(int)

                aggregateMID = pd.DataFrame(DataIn.median()).transpose()
                aggregateMID.round(0).astype(int)

                aggregateMIN = pd.DataFrame(DataIn.min()).transpose()
                aggregateMIN.round(0).astype(int)
                
                aggregateMAX = pd.DataFrame(DataIn.max()).transpose()
                aggregateMAX.round(0).astype(int)
                
                DidAggregation = 1
                
            except:
                
                DoingZero = -99
                'return -99'
                
                pass
        
    if (DidAggregation == 1):
        
        #now insert the statistics into the minute2send
        minute2send.loc[0,'year'] = aggregateMID.loc[0,'year'] # time
        minute2send.loc[0,'month'] = aggregateMID.loc[0,'month']
        minute2send.loc[0,'day'] = aggregateMID.loc[0,'day']
        minute2send.loc[0,'hour'] = aggregateMID.loc[0,'hour']
        minute2send.loc[0,'minute'] = aggregateMID.loc[0,'minute']
        
        minute2send.loc[0,'COUNT'] = aggregateCNT.loc[0,'pm2_5'] #count
        
        minute2send.loc[0,'AVGpm1_0'] = aggregateAVG.loc[0,'pm1_0'] #avg pm
        minute2send.loc[0,'AVGpm2_5'] = aggregateAVG.loc[0,'pm2_5']
        minute2send.loc[0,'AVGpm10'] = aggregateAVG.loc[0,'pm10']
        
        minute2send.loc[0,'AVGT_C'] = -99
        minute2send.loc[0,'AVGrh'] = -99
        
        minute2send.loc[0,'STDpm1_0'] = (aggregateSTD.loc[0,'pm1_0']) * 100 #pm std * 100
        minute2send.loc[0,'STDpm2_5'] = (aggregateSTD.loc[0,'pm2_5']) * 100
        minute2send.loc[0,'STDpm10'] = (aggregateSTD.loc[0,'pm10']) * 100
        
        minute2send.loc[0,'STDT_C'] = -99
        minute2send.loc[0,'STDrh'] = -99
        
        minute2send.loc[0,'MINpm1_0'] = aggregateMIN.loc[0,'pm1_0'] #pm 3 point
        minute2send.loc[0,'MEDIANpm1_0'] = aggregateMID.loc[0,'pm1_0']
        minute2send.loc[0,'MAXpm1_0'] = aggregateMAX.loc[0,'pm1_0']
        
        minute2send.loc[0,'MINpm2_5'] = aggregateMIN.loc[0,'pm2_5'] #pm 3 point
        minute2send.loc[0,'MEDIANpm2_5'] = aggregateMID.loc[0,'pm2_5']
        minute2send.loc[0,'MAXpm2_5'] = aggregateMAX.loc[0,'pm2_5']

        minute2send.loc[0,'ZERO_on'] = DoingZero
        
    else:
        
        logger.info('Did not do statistics for ENVIDAS')
        
        pass
    
    
    return(minute2send)

#######d##################################
#(4) setup header & modbus data storage
#########################################
fleHeader = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "DataHeader.txt")
    
PMheader = ["year", "month", "day", "hour", "minute", "second",
            "pm1_0", "pm2_5", "pm10",
            "gt03um", "gt05um", "gt1_0um", "gt2_5um", "gt5_0um", "gt10um",
            "zero"]

HeaderLine = ",".join(PMheader) + "\n"

with open(fleHeader, "a") as myfile:
    myfile.write(HeaderLine)

#aggregated data header
fleHeader = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "ENVIDASHeader.txt")

ENVIDASheader = ["year", "month", "day", "hour", "minute",
                 "COUNT",
                 "AVGpm1_0", "AVGpm2_5", "AVGpm10",
                 "AVGT_C","AVGrh", 
                 "STDpm1_0", "STDpm2_5", "STDpm10",
                 "STDT_C", "STDrh",
                 "MINpm1_0", "MEDIANpm1_0", "MAXpm1_0",
                 "MINpm2_5", "MEDIANpm2_5", "MAXpm2_5",
                 "ZERO_on"]

HeaderLine = ",".join(ENVIDASheader) + "\n"

with open(fleHeader, "a") as myfile:
    myfile.write(HeaderLine)
               
#server data structure
fleoutAVG = (DataOutDirectory + site + '_' + sensorType + "_sn" + sn + "_" + "1Min.txt")
SetupDataFile(fleoutAVG, "a")

#&initialize
InitData = pd.DataFrame(0, index=range(0,1),columns=ENVIDASheader)

try:
    with open(fleoutAVG, 'w') as myfile:
        InitData.to_csv(myfile, header=False, index=False)
except:
    logger.info("Server data.csv did not initalize.")
  

########################################
## (5) Check zero pin functionality
#########################################
#check if this is a zero 
try:
    pinhigh = GPIO.input(21)
except:
    logger.info("PMSX003 code set the zero pin to low.")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.OUT)
    GPIO.output(21, GPIO.LOW)
    pinhigh = 0
            
########################################
## (6) On RPi storage - daily records
#########################################
DateStr4Out = str(datetime.datetime.now().day) + '_' + str(datetime.datetime.now().month) + '_' + str(datetime.datetime.now().year)
        
fleoutFSTDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1sec" + DateStr4Out + ".txt")
SetupDataFile(fleoutFSTDaily, "a")       
        
fleoutAVGDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min" + DateStr4Out + ".txt")
SetupDataFile(fleoutAVGDaily, "a")

#########################################
# (6) Connect to sensor
#########################################
ser, ConnectionError = plantower_serial_connection(Port2Focus)

if (ConnectionError == 'none'):
    logger.info("Connected to " + sensorType) 
else:
    ### Give up and report the failure
    logger.info("Exiting " + sensorType + " connection: " + str(ConnectionError)) 
    sys.exit(1) #exit 

########################################
# (7) Read serial data from plantower
########################################
#Initialize 
iter = 0

MeasureTime = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
Day_previous = MeasureTime.day
minute_past  = MeasureTime.minute

#Initiate a dataframe for the incoming data
DataIn = pd.DataFrame(np.nan, index=range(0,1),columns=PMheader)

IndRow = 0
 
while True:
    try:
        #sets sampling rate
        time.sleep(SampleRate) 
        
        #time - should not observe daylight savings
        MeasureTime = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
        
        #make a serial read and then error check it
        rcv, Elaspsed, BaseErrorFlag = read_pm_line(ser) #read in serial data   
        rcv, ReadError, iter = read_pm_error_check(rcv, Elaspsed, BaseErrorFlag, iter)
        
        #check if this is a zero
        try:
            pinhigh = GPIO.input(21)
        except:
            logger.info("Error: PMSX003 code cannot access zero pin.  Assumed no zero")
            pinhigh = 0
            
        #package data 
        if (ReadError == 'none'):
            #Parse rcv serial string to DataIn: see PMS5003st manual for var. assignments
            DataIn.ix[IndRow,0]  = int(MeasureTime.year)        #time block
            DataIn.ix[IndRow,1]  = int(MeasureTime.month)
            DataIn.ix[IndRow,2]  = int(MeasureTime.day)
            DataIn.ix[IndRow,3]  = int(MeasureTime.hour)
            DataIn.ix[IndRow,4]  = int(MeasureTime.minute)
            DataIn.ix[IndRow,5]  = int(MeasureTime.second)
                
            DataIn.ix[IndRow,6]  = int(rcv[10] * 256 + rcv[11])    #pm block
            DataIn.ix[IndRow,7]  = int(rcv[12] * 256 + rcv[13])                
            DataIn.ix[IndRow,8]  = int(rcv[14] * 256 + rcv[15])                           
                   
            DataIn.ix[IndRow,9] = int(rcv[16] * 256 + rcv[17]) #gt block
            DataIn.ix[IndRow,10] = int(rcv[18] * 256 + rcv[19])
            DataIn.ix[IndRow,11] = int(rcv[20] * 256 + rcv[21])
            DataIn.ix[IndRow,12] = int(rcv[22] * 256 + rcv[23])
            DataIn.ix[IndRow,13] = int(rcv[24] * 256 + rcv[25])
            DataIn.ix[IndRow,14] = int(rcv[26] * 256 + rcv[27])
            
            DataIn.ix[IndRow,15] = int(pinhigh) #zero
            
            #add 1 to row index for next loop
            IndRow += 1 
            
        elif (ReadError != 'none') & (ReadError == 'ErrFlag1'):
            #actions = reset connection & try again
            ser, ConnectionError = plantower_serial_connection(Port2Focus)
            logger.info("Error: Restarting Connection")  
        
        elif (ReadError != 'none') & (ReadError == 'ErrFlag2'):
            #Can't fix connection: give up
            logger.info("## Exiting!  N try > max")
            ser.close() # close the serial connection
            sys.exit(1) #exit the program
            
        else: 
            #Can't fix connection: give up
            logger.info("## Exiting!  N try > max")
            ser.close() # close the serial connection
            sys.exit(1) #exit the program
        
        ############################################################
        #1 min. interval
        ############################################################
        #save data to disk
        minute_current = MeasureTime.minute
        
        if (minute_current != minute_past):
            
            #Reset the minute for record keeping
            minute_past = minute_current
            
            #do the ENVIDAS aggregation
            minute2send = Aggregate2Send(DataIn, ENVIDASheader)
            
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
                
            ####### Reset RPi-sensor connection - aligns serial read with current time 
            ser, ConnectionError = plantower_serial_connection(Port2Focus)

            #Reset DataIn for incoming data
            IndRow = 0
            DataIn = pd.DataFrame(np.nan, index=range(0,1),columns=PMheader)
            
            
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
        logger.info("Closing " + Port2Focus + " exiting.") 
        
        ser.close() # close the serial connection
        
        sys.exit(1) # exit the program
        


