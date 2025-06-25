#Functions to check if RPi is working OK
#updated by awf - 7/26/2019

#functions
def StopRunPMShell():
    
    WhatsUPandRUNNING = subprocess.run(['pgrep', '-a','python3.5'], stdout=subprocess.PIPE)
    WhatsUPandRUNNING = WhatsUPandRUNNING.stdout.decode("utf-8")
    PythonPIDs = WhatsUPandRUNNING.split('\n')
    
    for iPID in PythonPIDs:    
        Check4WatchDog = iPID.find('WatchDog')
        if(Check4WatchDog == -1):
            try:
                pid2stop = iPID.split()[0]
                ERRtrap = subprocess.run(['kill', pid2stop], stderr=subprocess.PIPE)
                
                #if the process did not close, ask the kernal to stop it
                time.sleep(0.5)
                try:
                    ERRtrap = subprocess.run(['kill', '-9', pid2stop], stderr=subprocess.PIPE)
                except:
                    pass
                
            except:
                pass
            

def IsLateMeasurement(LateInMinutes):
    
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



#change this to the server ip
def CheckInternet(ServerToCheck):
    
    InternetUp = subprocess.run(['ping', '-c', '1', '-w', '1', ServerToCheck], stdout=subprocess.PIPE)
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