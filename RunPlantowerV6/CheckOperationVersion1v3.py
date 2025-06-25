#collection of functions to check
#if the sensor box is working
#this script includes a check for the button programs; builds that do not include a UPS

#(0) libraries
import sys
import subprocess, os
import datetime, time
import RPi.GPIO as GPIO 

#(1) check if the computer can reach the modem?
def CheckInternet(ip2ping):
    
    InternetUp = subprocess.run(['ping', '-c', '1', '-w', '1', ip2ping], stdout=subprocess.PIPE)
    InternetUp = InternetUp.stdout.decode("utf-8")

    try:
        #look if any ping packets were lost 
        stloss = InternetUp.find("received,") + 9
        edloss = InternetUp.find("% packet loss")
        PacketLoss = InternetUp[stloss:edloss]
        
        #convert % packet loss to a number
        PacketLoss = float(PacketLoss)
        
    except:
        
        PacketLoss = 1 #assume the internet is down
        
    return(PacketLoss)

#(2)check most recent measurements to determine if they are current
def IsLateMeasurement(root, FleInDir, LateInMinutes):
    
    nUpdatedFiles = 0
    
    for items in FleInDir:
        
        WhatFle = items.find('1Min.txt')
        
        if (WhatFle != -1):
            LateTime = datetime.datetime.utcnow() - datetime.timedelta(hours=8) - datetime.timedelta(minutes=LateInMinutes)
            
            #get the output data
            try:
                iCSVfile = root + items
                
                with open(iCSVfile, "r") as myfile:
                    PtowerDATA = myfile.readlines()[-1] #-1 = last line
                    
                PtowerDATA = PtowerDATA.split(',')
                
                MeasurementTime = datetime.datetime(year = int(PtowerDATA[0]),
                                                    month = int(PtowerDATA[1]),
                                                    day = int(PtowerDATA[2]),
                                                    hour = int(PtowerDATA[3]),
                                                    minute = int(PtowerDATA[4]))
                
                if (MeasurementTime > LateTime):
                    nUpdatedFiles+=1
                    
            except:
                
                nUpdatedFiles+=0
    
    return(nUpdatedFiles)

   

#(3) function to stop python scripts from shell
def RestartRunPMShell(restartScripts):
    
    #wrap statements in a function 
    def RemoveSensorScripts():
        
        for iPID in PythonPIDs:
            #Do not stop the watchdog program
            Check4WatchDog = iPID.find('WatchDog')
            Check4InternetUp = iPID.find('InternetUp')
            
            if((Check4WatchDog == -1) & (Check4InternetUp == -1)):
                try:
                    pid2stop = iPID.split()[0]
                    ERRtrap = subprocess.run(['sudo', 'kill', pid2stop], stderr=subprocess.PIPE)
                    
                    #if the process did not close, ask the kernal to stop it
                    time.sleep(0.5)
                    try:
                        ERRtrap = subprocess.run(['sudo', 'kill', '-9', pid2stop], stderr=subprocess.PIPE)
                    except:
                        pass
                    
                except:
                    pass
                
    WhatsUPandRUNNING = subprocess.run(['pgrep', '-a','python3.9'], stdout=subprocess.PIPE)
    WhatsUPandRUNNING = WhatsUPandRUNNING.stdout.decode("utf-8")
    PythonPIDs = WhatsUPandRUNNING.split('\n')
            
    #restart shell
    RemoveSensorScripts()
    ERRtrapPMShell = subprocess.Popen([restartScripts], stderr=subprocess.PIPE)
          
#two types of alerts
def AlertOPpause(nROLLS):
    for i in range(nROLLS):
        time.sleep(1)
        GPIO.output(21, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(21, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(21, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(21, GPIO.LOW)
        
        
def AlertOPcontinue(nROLLS):
    for i in range(nROLLS):
        time.sleep(0.1)
        GPIO.output(21, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(21, GPIO.LOW)