import tkinter as tk
from tkinter import ttk
import threading
import time
import serial
import os
import sys
import logging
import pandas as pd
import RPi.GPIO as GPIO
from datetime import datetime

# The existing sensor code starts here
# (Assume this part is unchanged and already implemented in your script)
#########################################  
#(1) input from shell & adjust here
#########################################
#site = sys.argv[1]
site = "Test"

##
#sn = sys.argv[2]
sn = "324"

##
#Port2Focus = sys.argv[3]
Port2Focus = "ttyAMA1"

# uncomment for testing
site="BOX"
sn="2"
Port2Focus="ttyAMA1"

#adjust here
code_version = 4
sensorType = "PMS5003st"
DataOutDirectory = "/media/particulatepi/data/PMoutputData/" #output directory

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
# connect to the sensor
def plantower_serial_connection(_serPort):
    '''Establishes serial connection between RPi and plantower:
    inputs: _serPort = RPi port attached to plantower
    
    returns: ser = serial object for the plantower connection
    ErrorFlag = error message associated with a failed serial connection w/"none" == no errors/connection is OK''' 
    
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
            
            ser.open()
            IsPortOpen = ser.is_open
            ErrorFlag = 'none'
            
        except:
            
            nTrys += 1
            logger.info('Could not make a serial object.')
            time.sleep(1)#pause
    
    return(ser, ErrorFlag)


# read in the serial string from the plantower and do basic QA/QC
def read_pm_line(_port):
    '''Reads serial data from plantower
    inputs: _port = serial object from plantower_serial_connection
    
    return:
    rv is the data (serial string) from the plantower
    error_read_pm_line = error message associated with a failed serial read w/ "none" == all OK'''
    
    #initialize
    nSearchForStartReads = 0
    rv = b''
    error_read_pm_line = 'error_read_pm_line'
    
    #do the read
    while ((error_read_pm_line != 'none') & (nSearchForStartReads < 100)):
        try:
            nSearchForStartReads += 1
            
            #PMS5003st gives a 40 character string
            ch1 = _port.read()
            if ch1 == b'\x42':
                ch2 = _port.read()
                if ch2 == b'\x4d':
                    rv += ch1 + ch2
                    rv += _port.read(38)
                    
                    error_read_pm_line = 'none'

        except:
            rv = b''
            
    return(rv, error_read_pm_line)
            
# error check for incoming serial data          
def read_pm_error_check(rv, error_read_pm_line):
    '''Error checking on read_pm_line'''
    
    err_check = error_read_pm_line
    
    ##check if a base error was thrown
    if (error_read_pm_line != 'none'):
        logger.info('error_read_pm_line')
        err_check = 'err_flag'
    ##did not get a read
    if (rv == b''):
        logger.info('EmptyReadLine')
        err_check = 'err_flag'
    ##length 
    if (len(rv) != 40):
        logger.info('ReadLineLengthError')
        err_check = 'err_flag'
    ##check sum 
    if (len(rv) == 40):
        DataSum = sum(rv[0:37])
        cksum = (rv[38] * 256 + rv[39])
        if (DataSum != cksum):
            logger.info('CheckSumFailError')
            err_check = 'err_flag'
    
    return(rv, err_check)
    
# file management - check read-write      
def SetupDataFile(fleOut, writetype):
    '''check file permissions'''
    
    if os.path.exists(fleOut) == True:
        logger.info('Restarting Run: Appending data to' + fleOut) 
    else:
        try:
            file2write = open(fleOut, writetype)
            file2write.close()
        except:
            logger.info('Setup file Error')
            
        OKfilePermission = (os.access(fleOut, os.R_OK)) & (os.access(fleOut, os.W_OK)) #read-write privaleges?
        if (OKfilePermission == False):
            logger.info('File Permission Error: ' + fleOut + ' Exiting!') 
            sys.exit(1) #exit


def init_dataout(fleoutAVG, PMheader):
    '''init data to file'''
    
    InitData = pd.DataFrame(999, index=range(0,1), columns = PMheader) # initialize

    try:
        with open(fleoutAVG, 'w') as myfile:
            InitData.to_csv(myfile, header=False, index=False)
    except:
        logger.info("data.csv did not initalize.")
  
  
#######d##################################
#(4) write the header to disk
#########################################
fleHeader = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "DataHeader.txt")
    
PMheader = ["year", "month", "day", "hour", "minute", "second",
            "apm1_0", "apm2_5", "apm10",
            "pm1_0", "pm2_5", "pm10",
            "gt03um", "gt05um", "gt1_0um", "gt2_5um", "gt5_0um", "gt10um",
            "form",
            "T_K",
            "rh", "zero",
            "code_version", "sn"]

HeaderLine = ",".join(PMheader) + "\n"

with open(fleHeader, "a") as myfile:
    myfile.write(HeaderLine)
               
######################################################################
## (5) On RPi storage - daily records & init minute data for shipping
######################################################################
DateStr4Out = str(datetime.datetime.now().day) + '_' + str(datetime.datetime.now().month) + '_' + str(datetime.datetime.now().year)
        
fleoutFSTDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1sec" + DateStr4Out + ".txt")
SetupDataFile(fleoutFSTDaily, "a")       
        
fleoutAVGDaily = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min" + DateStr4Out + ".txt")
SetupDataFile(fleoutAVGDaily, "a")

# setup the file for data that will be loaded to the modbus server - this will get updated every minute
fleoutAVG = (DataOutDirectory + site + '_' + sensorType + "_sn" + sn + "_" + "1Min.txt")
SetupDataFile(fleoutAVG, "a")
init_dataout(fleoutAVG, PMheader)

########################################
## (6) check zero 
#########################################
 
try:
    pinhigh = GPIO.input(21)
except:
    logger.info("PMS5003st code set the zero pin to low.")
    GPIO.setmode(GPIO.BCM) # updated BCM to BOARD 12SEP2023
    GPIO.setup(21, GPIO.OUT)
    GPIO.output(21, GPIO.LOW)
    pinhigh = 0
    
#########################################
# (7) Connect to sensor
#########################################
ser, ConnectionError = plantower_serial_connection(Port2Focus)

if (ConnectionError == 'none'):
    logger.info("Connected to " + sensorType) 
else:
    ### Give up and report the failure
    logger.info("Exiting " + sensorType + " connection: " + str(ConnectionError)) 
    sys.exit(1) #exit 

########################################
# (8) Read serial data from plantower
########################################
#Initialize
iter = 0
MeasureTime = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
Day_previous = MeasureTime.day
minute_past  = MeasureTime.minute

#Initiate a dataframe for the incoming data
DataIn = pd.DataFrame(999, index=range(0,1),columns=PMheader)

IndRow = 0
 
while True:
    try:
        
        #sets sampling rate
        time.sleep(SampleRate) 
            
        #time - should not observe daylight savings
        MeasureTime = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
        
        #Clear input buffer to avoid lagging, was done after each minute before
        ser.flushInput()
        
        rcv, error_read_pm_line = read_pm_line(ser) #read in serial data
        
        # for troubleshooting
        # print(rcv)
        
        rcv, read_error = read_pm_error_check(rcv, error_read_pm_line)

        # for troubleshooting
        # print(rcv)
        # print(read_error)
        
        if (read_error == 'none'):
            #Parse rcv serial string to DataIn: see PMS5003st manual for var. assignments
            DataIn.loc[IndRow,"year"]  = int(MeasureTime.year)        #time block
            DataIn.loc[IndRow,"month"]  = int(MeasureTime.month)
            DataIn.loc[IndRow,"day"]  = int(MeasureTime.day)
            DataIn.loc[IndRow,"hour"]  = int(MeasureTime.hour)
            DataIn.loc[IndRow,"minute"]  = int(MeasureTime.minute)
            DataIn.loc[IndRow,"second"]  = int(MeasureTime.second)
                
            DataIn.loc[IndRow,"apm1_0"]  = int(rcv[4] * 256 + rcv[5])    #apm block
            DataIn.loc[IndRow,"apm2_5"]  = int(rcv[6] * 256 + rcv[7])                
            DataIn.loc[IndRow,"apm10"]  = int(rcv[8] * 256 + rcv[9])                
                
            DataIn.loc[IndRow,"pm1_0"]  = int(rcv[10] * 256 + rcv[11])  #pm block
            DataIn.loc[IndRow,"pm2_5"] = int(rcv[12] * 256 + rcv[13])             
            DataIn.loc[IndRow,"pm10"] = int(rcv[14] * 256 + rcv[15])              
                   
            DataIn.loc[IndRow,"gt03um"] = int(rcv[16] * 256 + rcv[17]) #gt block
            DataIn.loc[IndRow,"gt05um"] = int(rcv[18] * 256 + rcv[19])
            DataIn.loc[IndRow,"gt1_0um"] = int(rcv[20] * 256 + rcv[21])
            DataIn.loc[IndRow,"gt2_5um"] = int(rcv[22] * 256 + rcv[23])
            DataIn.loc[IndRow,"gt5_0um"] = int(rcv[24] * 256 + rcv[25])
            DataIn.loc[IndRow,"gt10um",] = int(rcv[26] * 256 + rcv[27])
                   
            DataIn.loc[IndRow,"form"] = int(((rcv[28] * 256 + rcv[29])/1000))  #formaldehyde
                
            # there is a multiplier = 10 from the plantower
            DataIn.loc[IndRow,"T_K"] = int(round((((struct.unpack('>20h',rcv)[15])/10) + 273.15) * 10, 0))  #temp in Kelvin
            
            DataIn.loc[IndRow,"rh"] = int(rcv[32] * 256 + rcv[33]) #rh * 10
            
            DataIn.loc[IndRow,"zero"] = int(GPIO.input(21)) #zero
            
            DataIn.loc[IndRow,"code_version"] = int(code_version) # version of code
            DataIn.loc[IndRow,"sn"] = int(sn) # sn
            
            #add 1 to row index for next loop
            IndRow += 1 
            
            # reset iter
            iter = 0
            
        elif ((read_error != 'none') & (iter > 50) & (iter <= 99)):
            ser, ConnectionError = plantower_serial_connection(Port2Focus)
            logger.info("Error: Restarting Connection")
            
            iter += 1
            
        elif ((read_error != 'none') & (iter > 99)):
            logger.info("## N try > 99, writing 999 to data")
            init_dataout(fleoutAVG, PMheader) # write out 999 to minute data on exit

        else:
            iter+=1

            
        ############################################################
        #(9) write data at 1 min. interval
        ############################################################
        #save data to disk
        minute_current = MeasureTime.minute
        
        if (minute_current != minute_past):
            
            minute2send = pd.DataFrame(999, index=range(0,1), columns=PMheader)
  
            try:
                #do the ENVIDAS aggregation
                
                minute2send.loc[0,"apm1_0"] = DataIn["apm1_0"].mean().round(0) #avg apm mass
                minute2send.loc[0,"apm2_5"] = DataIn["apm2_5"].mean().round(0)
                minute2send.loc[0,"apm10"] = DataIn["apm10"].mean().round(0)
                
                minute2send.loc[0,"pm1_0"] = DataIn["pm1_0"].mean().round(0) #avg pm mass
                minute2send.loc[0,"pm2_5"] = DataIn["pm2_5"].mean().round(0)
                minute2send.loc[0,"pm10"] = DataIn["pm10"].mean().round(0)
                
                minute2send.loc[0,"gt03um"] = DataIn["gt03um"].mean().round(0)  #avg particle counts
                minute2send.loc[0,"gt05um"] = DataIn["gt05um"].mean().round(0)
                minute2send.loc[0,"gt1_0um"] = DataIn["gt1_0um"].mean().round(0)
                minute2send.loc[0,"gt2_5um"] = DataIn["gt2_5um"].mean().round(0)
                minute2send.loc[0,"gt5_0um"] = DataIn["gt5_0um"].mean().round(0)
                minute2send.loc[0,"gt10um"] = DataIn["gt10um"].mean().round(0)
                
                minute2send.loc[0,"form"] = DataIn["form"].mean().round(0) #avg formaldehyde
                minute2send.loc[0,"T_K"] = DataIn["T_K"].mean().round(0) #avg temp
                minute2send.loc[0,"rh"] = DataIn["rh"].mean().round(0) #avg rh
                
                minute2send.loc[0,"zero"] = DataIn["zero"].mean().round(0) #doing zero
                
                minute2send.loc[0,"code_version"] = DataIn["code_version"].median().round(0) #code version
                minute2send.loc[0,"sn"] = DataIn["sn"].median().round(0) #sn
                
                minute2send.loc[0,"year"] = DataIn["year"].median().round(0) # time
                minute2send.loc[0,"month"] = DataIn["month"].median().round(0)
                minute2send.loc[0,"day"] = DataIn["day"].median().round(0)
                minute2send.loc[0,"hour"] = DataIn["hour"].median().round(0)
                minute2send.loc[0,"minute"] = DataIn["minute"].median().round(0)
                minute2send.loc[0,"second"] = DataIn["second"].median().round(0)
                
            except:
                logger.info("Minute could not be averaged. May be empty.")
            
            #Reset the minute for record keeping
            minute_past = minute_current
              
            try:
                with open(fleoutAVG, 'w') as myfile1:
                    minute2send.to_csv(myfile1, header=False, index=False, float_format='%.0f')
                    
                with open(fleoutAVGDaily, "a") as myfile2:
                    minute2send.to_csv(myfile2, header=False, index=False, float_format='%.0f')
                    
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
                    
            else:
                logger.info("Low disk space. Stopped logging data to local site")
                
            #Reset DataIn for incoming data
            IndRow = 0
            DataIn = pd.DataFrame(np.nan, index=range(0,1),columns=PMheader)
            
        ############################################################
        #(10) new file every day
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
            
    except:
        
        logger.info("!!Crashed!!")
        init_dataout(fleoutAVG, PMheader) # write out 999 to minute data on exit
        ser.close() # close the serial connection
        sys.exit(1) # exit the program
        
# Tkinter GUI code
class ParticulateSensorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Particulate Sensor Data")

        # Create a table to display data
        self.tree = ttk.Treeview(root, columns=("Parameter", "Value"), show="headings")
        self.tree.heading("Parameter", text="Parameter")
        self.tree.heading("Value", text="Value")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Add parameters to the table
        self.parameters = ["PM1.0 (ug/m3)", "PM2.5 (ug/m3)", "PM10 (ug/m3)", "HCHO (mg/m3)", "Temp (C)", "RH (%)"]
        for param in self.parameters:
            self.tree.insert("", "end", iid=param, values=(param, "--"))

        # Start the update loop
        self.update_interval = 1000  # 1 second
        self.running = True
        self.update_loop()

    def update_data(self, data):
        for param, value in data.items():
            if param in self.parameters:
                self.tree.item(param, values=(param, value))

    def update_loop(self):
        if self.running:
            # Example: Replace `get_sensor_data()` with actual data from your sensor
            sensor_data = get_sensor_data()  # Mock function
            self.update_data(sensor_data)
            self.root.after(self.update_interval, self.update_loop)

    def stop(self):
        self.running = False

# Function to integrate GUI with the sensor code
def start_gui():
    root = tk.Tk()
    gui = ParticulateSensorGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        gui.stop()

# Example of how to get sensor data (replace with actual implementation)
def get_sensor_data():
    global PM1, PM2_5, PM10, HCHO, TEMP, RH  # These should be updated by your existing code
    return {
        "PM1.0 (ug/m3)": PM1,
        "PM2.5 (ug/m3)": PM2_5,
        "PM10 (ug/m3)": PM10,
        "HCHO (mg/m3)": HCHO,
        "Temp (C)": TEMP,
        "RH (%)": RH,
    }

# Start the GUI in a separate thread
if __name__ == "__main__":
    # Start the GUI in a separate thread to avoid blocking the main loop
    gui_thread = threading.Thread(target=start_gui, daemon=True)
    gui_thread.start()

    # Main loop for sensor reading
    try:
        while True:
            # Your existing code to read and process sensor data
            time.sleep(1)  # Replace with the actual sensor data polling interval
    except KeyboardInterrupt:
        print("Exiting program...")
