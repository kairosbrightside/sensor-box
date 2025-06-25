#!/bin/bash
#shell for monitoring RPi uptime

################################################
################################################
#make sure the programs are executable
#sudo chmod 755 /home/pi/Desktop/RunPlantower/StartUpWatchDogVersion1v3.py
#sudo chmod 755 /home/pi/Desktop/RunPlantower/CheckInternetUpVersion1v3.py
#sudo chmod 755 /home/pi/Desktop/RunPlantower/CheckOperationVersion1v3.py

WatchDog='/home/particulatepi/RunPlantower/StartUpWatchDogVersion1v4.py'
CheckInternet='/home/particulatepi/RunPlantower/CheckInternetUpVersion1v3.py'


#execute the scripts
/usr/bin/python3.9 $WatchDog "0" &
/usr/bin/python3.9 $CheckInternet &
#/usr/bin/python3.9 $RunButton &