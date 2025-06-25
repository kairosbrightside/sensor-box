#Watchdog to check if the sensor package started correctly
#alerts OP if box is working or not

##WORKING == 20 quick continuous pump buzzes
##NOT WORKING == 5 syncopated pump buzzes

#Check @ startup includes:
#(1) Check if the internet is working
#(2) Check if all key python scripts started
#(3) Check if the data that is being written to file is current with RPi time

#This script was modified to check if the button script is running

#Change as needed:
RunPMShell = '/home/particulatepi/RunPlantower/RunPMShellVersion1v3.sh'
DataDir = '/media/particulatepi/data/PMoutputData' #Where is the data stored?
ip2ping = '192.168.13.101'      #Modem gateway connected to RPi?
#ip2ping = '192.168.1.1'      #Modem gateway connected to RPi?

#libraries
import sys
import subprocess, os
import datetime, time
import RPi.GPIO as GPIO 

import CheckOperationVersion1v3 as CheckOP

#main
def doWatchDog(print2screen):
    if (print2screen == 1):
        print('Print diagnostics to screen:')
                
    #(0) Init
    #setup GPIO pins
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.OUT)

    #tell the OP that the box started the watchdog
    CheckOP.AlertOPpause(1)
    
    #init parameters for checks; 0 = off; 1 = on
    InternetUp = 0
    ScriptsUp = 0
    FilesUp = 0

    ### Main script ###
    #(1) Check if the box is connected to the internet
    if (print2screen == 1):
        print('Is the internet up:')
        
    FailedConnection = 0
    nTry = 60 # 0.5 min. trys

    while(InternetUp == 0):
        
        time.sleep(1) 
        
        PacketLoss = CheckOP.CheckInternet(ip2ping)
            
        if(PacketLoss == 0):
            InternetUp = 1
            if (print2screen == 1):
                print('Internet OK')
        else:
            InternetUp = 0
            FailedConnection += 1
        
        #try restarting networking if the internet is down
        if(FailedConnection == round(nTry/2)):
            try:
                if (print2screen == 1):
                    print('Could not ping modem:')
                    print('restart network connection')
                subprocess.run(['systemctl', 'restart', 'networking'])
            except:
                pass
        
        #alert OP if we did not establish a connection
        if(FailedConnection >= nTry):
            if (print2screen == 1):
                print('no connection')
            break
            
    #(2)Check if all the python programs started up?
    if (print2screen == 1):
        print('Check if scripts are running:')
                    
    FailedScript = 0
    nTry = 10 # 120 trys - 2 minutes

    while(ScriptsUp == 0):
        
        PythonUpTEMP = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE) #will this close itself?
        PythonUp = subprocess.check_output(['grep', 'python3.5'], stdin=PythonUpTEMP.stdout)
        PythonUp = PythonUp.decode("utf-8")

        serverStart = PythonUp.find("UpdateServer")
        plantowerStart = PythonUp.find("PMS5003stVersion")
        serialConnectionStart = PythonUp.find("serial0")
        usbConnectionStart = PythonUp.find("ttyUSB")
        zeroStart = PythonUp.find("DoZero")
        buttonStart = PythonUp.find("Button")
        
        #if any of the scripts are not running, kill all python processes and then restart them
        if((serverStart == -1)|(plantowerStart == -1)|(serialConnectionStart == -1)|(usbConnectionStart == -1)|(zeroStart == -1)|(buttonStart == -1)):
                
            CheckOP.RestartRunPMShell(RunPMShell)   
            
            FailedScript+=1
            
            if (print2screen == 1):
                print('script error: restarting scripts')
            
            time.sleep(15)
            
        else:
            ScriptsUp = 1
            if (print2screen == 1):
                print('scripts OK')
            
        #shutdown if we could not establish a connection
        if FailedScript >= nTry:
            if (print2screen == 1):
                print('scripts not running')
            break
        
    #(3) Check if current data is written to file
    if (print2screen == 1):
        print('Check if the data are current:')
        
    FleInDir = os.listdir(DataDir)
    WhatIsLateInMin = 2 # it takes around 3 minutes to assure an update

    #How many 1 Min files are there?
    HowManyFilesShouldBeUpdated = 0

    #Get the number of files that should be updated
    for items in FleInDir:
        WhatFle = items.find('1Min.txt')
        if(WhatFle != -1):
            HowManyFilesShouldBeUpdated+=1

    #How many of these files are updated?
    FailedUpdate = 0
    nTrys = 100

    while (FilesUp == 0):
        
        nUpdatedFiles = CheckOP.IsLateMeasurement(DataDir, FleInDir, WhatIsLateInMin)
        
        if(nUpdatedFiles == HowManyFilesShouldBeUpdated):
            if (print2screen == 1):
                print('Data OK')
            FilesUp = 1
        else:
            FilesUp = 0
            
        #restart shell if proc are not updating
        if ((FilesUp == 0) & (FailedUpdate == (nTrys/2))):
            
            CheckOP.RestartRunPMShell(RunPMShell)
            
            if (print2screen == 1):
                print('Data not current: try restarting scripts')
                
            time.sleep((WhatIsLateInMin*60)/nTrys) #equally spaced effort
            
        if ((FilesUp == 0) & (FailedUpdate > nTrys)):
            if (print2screen == 1):
                print('Data not current: giving up - check plantower connections')
            break
        
        FailedUpdate+=1 
        time.sleep((WhatIsLateInMin*60)/nTrys)
        
        
    #(4)Alert the tech that the box started up OK or not
    ## if not --> shutdown
    if (InternetUp == 1) & (ScriptsUp == 1) & (FilesUp == 1):
        CheckOP.AlertOPcontinue(20) #long buzz to alert OP that everything is OK @ startup
        if (print2screen == 1):
            print('Sensor All OK')
    else:
        CheckOP.AlertOPpause(5)
        if (print2screen == 1):
            print('Sensor not working: action needed.')


#now do the watchdog
if(__name__ == '__main__'):
    
    #from shell
    print2screen = sys.argv[1]
    print2screen = int(print2screen)

    doWatchDog(print2screen)
    #GPIO.cleanup()
    
