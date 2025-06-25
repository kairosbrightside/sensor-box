# this script runs a modbus server on the raspberry pi
# please see:
# https://pymodbus.readthedocs.io/en/v1.3.2/examples/updating-server.html

# need to install pymodbus, twisted, and service_identity modules    
#---------------------------------------------------------------------------# 
#(1) import remaining libraries/modules that we need
#    libraries include datetime, time, pymodbus, twisted, and service_identity
#    insallation using python3.5 -m pip install XXXX from terminal window
#---------------------------------------------------------------------------#
import os, sys
import datetime, time

import logging

from pymodbus.server.async_copy import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

# 
from twisted.internet.task import LoopingCall

#---------------------------------------------------------------------------#
#(2) Setup: get inputs from shell & define output directories
#---------------------------------------------------------------------------#
DataOutDirectory = "/media/particulatepi/data/PMoutputData/" #output directory
sensorType = "PMS5003st"
delaytime = 5 # seconds 
RPiIP = '192.168.13.121' # IP address for Raspberry Pi & match modem
number_of_channels_per_sensor = 24 # this is the number of variables that we are sending per sensor

###inputs from shell
nInputsFromShell = len(sys.argv) - 1  #-1 accounts for the script name at 0
nSensor = int(nInputsFromShell/3) # n sensors

# directory to the most recent sensor data 
SensorDataDir  = [0] * nSensor

for ind in range(nSensor):
    
    ModbusPort = int(sys.argv[3])
    
    site = str(sys.argv[1])
    sn = str(sys.argv[(2 + (ind*3))])
    
    SensorDataDir[ind] = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min.txt") #Data dir from sensor
    
##### Uncomment for Troubleshooting
nSensor = 3
SensorDataDir  = [0] * nSensor
##
ModbusPort = int(5020)
##
site = "BOX"
##
sn1 = "1"
sn2 = "2"
sn3 = "3"
##
SensorDataDir[0] = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn1 + "_" + "1Min.txt")
SensorDataDir[1] = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn2 + "_" + "1Min.txt")
SensorDataDir[2] = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn3 + "_" + "1Min.txt")

#Zero call from ENVIDAS
ZeroCallFromENVIDAS = (DataOutDirectory + "ZeroCall" + ".txt")

######################################### 
#(2) create log
######################################### 
ServerfleLog = (DataOutDirectory + site + "_Server_" + "Log.txt")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s:%(levelname)s:%(levelno)s:%(message)s')

file_handler = logging.FileHandler(ServerfleLog)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

#---------------------------------------------------------------------------# 
#(3) Functions
#---------------------------------------------------------------------------#
def updating_writer(a):
    ''' A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    '''

    #---------------------------------
    # To server:
    #--------------------------------- 
    context  = a[0] #modbus context
    
    # value = 999 unless read data 
    nSensor = a[1]
    values = [int(999)] * (number_of_channels_per_sensor * nSensor)
    
    # this should be where the 1-min data is stored
    CSVdataLIST = a[2]
    
    for iSensor in range(nSensor):
        
        # adjust the starting point in Modbus context eg. iSensor 0 = 0; iSensor 1 = 24
        offset = iSensor * number_of_channels_per_sensor 
        
        iCSVfile = CSVdataLIST[iSensor] #1-min data 
        
        try:
            with open(iCSVfile, "r") as myfile:
                PtowerDATA = myfile.readlines()[-1] #-1 = last line 
        except:
            logger.info('Did not update server')
        
        # print(PtowerDATA) # uncomment for trouble shooting
        
        try:
            for iVar in range(number_of_channels_per_sensor):
                values[iVar + offset] = int(PtowerDATA.split(',')[iVar])
        except:
            logger.info('Error parsing plantower data to MODBUS format')
         
        # print(values) # uncomment for troubleshooting
  
    # Put bundled data into the modbus context using input registers starting at address 0
    register = 4 #input register
    slave_id = 0
    address  = 0 #start at 0
    context[slave_id].setValues(register, address, values)
  #  
    #---------------------------------
    # Recieving
    #---------------------------------
    ## record incoming zero call from ENVIDAS
    #register = 3
    #slave_id = 1
    #address = 0
    #i_doCal = context[slave_id].getValues(register, address, count=1)
    
    #Data2Recieve = a[3]
    
    #write the flag to disk
    #register = 4
    #slave_id = 0
    #address = 0zz
  
    #Data2Recieve = a[3]
    
    #i_doCal = 0 #context[slave_id].getValues(register, address, count=50)
    #print (str(i_doCal))
    #ZeroCallFromEnvidas = open(Data2Recieve, 'w+') # write over existing data  
    #ZeroCallFromEnvidas.write(str([i_doCal]))
    #ZeroCallFromEnvidas.close()
   

#print('Try to get cal from ENVIDAS')
#print(str(i_doCal))

# Initialize Modbus communication parameters
#register = 3  # Input register to read from
#slave_id = 0  # Slave ID
#address = 0   # Starting address
#count = 1     # Number of values to read

#try:
    # Attempt to retrieve values from the context
    #i_doCal = context[slave_id].getValues(register, address, count=count)
    #if not i_doCal:
        #raise ValueError("No values returned from getValues.")

    # File to receive data
    #Data2Recieve = a[3]  # Ensure `a[3]` is properly defined before this line

    # Write the flag to disk
    #with open(Data2Recieve, 'r+') as ZeroCallFromEnvidas:
        #ZeroCallFromEnvidas.write(str(i_doCal))
    
    #print('Try to get cal from ENVIDAS')
    #print(str(i_doCal))

#except KeyError as e:
    #print(f"KeyError: Context for slave_id={slave_id} is not initialized. Details: {e}")
#except ValueError as e:
    #print(f"ValueError: {e}")
#except Exception as e:
    #print(f"Unexpected error: {e}")
    
#---------------------------------------------------------------------------#
#initializations
#---------------------------------------------------------------------------#
# data store
nSpace = (nSensor * number_of_channels_per_sensor)

try:
        store = ModbusSlaveContext(
        di = ModbusSequentialDataBlock(0, [999]*nSpace),
        co = ModbusSequentialDataBlock(0, [999]*nSpace),
        hr = ModbusSequentialDataBlock(0, [0]*nSpace),
        ir = ModbusSequentialDataBlock(0, [999]*nSpace))
        context = ModbusServerContext(slaves=store, single=True)
except:
    logger.info('Failed initializing server')


# server information
try:
    identity = ModbusDeviceIdentification()
    identity.VendorName  = 'pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl   = 'http://github.com/bashwork/pymodbus/'
    identity.ProductName = 'pymodbus Server'
    identity.ModelName   = 'pymodbus Server'
    identity.MajorMinorRevision = '1.0'
except:
    pass

#---------------------------------------------------------------------------#
# run the server you want
#---------------------------------------------------------------------------#
logger.info('Starting Modbus Server')

#This updates the server
loop = LoopingCall(f=updating_writer, a=(context, nSensor, SensorDataDir, ZeroCallFromENVIDAS, ServerfleLog))
loop.start(delaytime) 

#try to start the modbus server 
nTry = 0 # counter for modbus server fails

while (nTry < 24):
    try:
        StartTcpServer(context, identity=identity, address=(RPiIP, ModbusPort))
    except:
        logger.info('Error: Restarting Modbus Server')
        time.sleep(60*15) # wait 15 minutes - based on validation criteria for hour
        
        nTry += 1
        
        if (nTry == 23):
            logger.info('No Longer Trying to Start the Server')
            sys.exit(1)

        
