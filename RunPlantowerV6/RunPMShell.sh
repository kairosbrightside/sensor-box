#!/bin/bash
#Config file for starting SensOR
#updated 09/15/2023 -ah/nk/lm/awf
#Updated by CRS 4/22/25


############################################################
############################################################
#Site-setup:
##modify for each site/sensor setup
############################################################
############################################################

#Site?
SITE="BOX"

#What are the serial numbers & associated ports for the plantowers?
SNPortPair=("1" "ttyAMA0"\
            "2" "ttyAMA1")

#Port for ENVIDAS communication?
ENVIDASPORT="5020"

############################################################
############################################################
##Notes for formating input:
############################################################
############################################################
##
##(1) SITE="SITE"
##
##(2) SNPortPair=("serialnumber1" "port1"/
##		  "serialnumber2" "port2")
## eg. SensorInfo = (SITE "11" "serial0" SITE "25" "ttyUSB0")
## says that plantower sn1 is hooked up on port1 and sn2 is hooked up on port2 
## FYI: serial0 = GPIO pins; ttyUSB0 = USB connection; ttyUSB1 = USB connection
## use lsusb and find /sys -name ttyUSB* at the linux console to explore

##(3) ENVIDASPORT = the port to exchange communication btw the RPi and ENVIDAS
##
## spaces and "" are important!

##Defaults: SITE="SITE"; SNPortPair=("1" "ttyUSB0" "2" "ttyUSB1"); ENVIDASPORT="5020"
## assumes 2 plantower connected to the RPi using a USB-to-serial connection
## and ENVIDAS is looking at port 5020 on the RPi for communications

############################################################
############################################################
##More extensive changes can be done below this section
##eg. Edit version of python code that will be executed, permissions,
##directory structure, default runs, etc
############################################################
############################################################
## Prep RPi

##(1) What python scripts do you want to run?
PlantowerScript='/home/particulatepi/RunPlantower/PMS5003stVersion4.py'
ZeroScript='/home/particulatepi/RunPlantower/DoZeroVersion1v4.py'
ServerScript='/home/particulatepi/RunPlantower/UpdateServerVersion3.py'
#ButtonScript='/home/particulatepi/RunPlantower/ButtonVersion1v3.py'
RestartScript='/home/particulatepi/RunPlantower/periodic_restart.py'
RPMScript='/home/particulatepi/RunPlantower/RPMCounter.py'
HeaterScript='/home/particulatepi/RunPlantower/HeaterControl.py'
NTPScript='/home/particulatepi/RunPlantower/CheckingNTP.py'
RebootSensor='/home/particulatepi/RunPlantower/PlantowerPowerControl.py'

#adjust permissions 
#sudo chmod 755 $PlantowerScript
#sudo chmod 755 $ZeroScript
#sudo chmod 755 $ServerScript

##(2) Check shell inputs from above, if wrong -> give default: 
#Do inputs exist?
if [ -z ${SITE+x} ]; then SITE="SITE"; fi
if [ -z ${SNPortPair+x} ]; then SNPortPair=("1" "serial0" "2" "ttyUSB0"); fi
if [ -z ${ENVIDASPORT+x} ]; then ENVIDASPORT="5020"; fi

#Check input number:
if [[ "${#SITE[@]}" != 1 ]]; then SITE=("SITE"); fi
nInputs="${#SNPortPair[@]}"; if [[ $((nInputs%2)) != 0 ]]; then SNPortPair=("1" "serial0" "2" "ttyUSB0"); fi
if [[ "${#ENVIDASPORT[@]}" != 1 ]]; then ENVIDASPORT=("5020"); fi

##(3) start scripts to read nSensor plantower(s):
nInputs="${#SNPortPair[@]}"
nSensor=$((nInputs / 2))

for (( i=0; i < nSensor; i+=1 )); do
	/usr/bin/python3.9 $PlantowerScript "${SITE[@]}" "${SNPortPair[(i*2)]}" "${SNPortPair[(i*2)+1]}" & 
done

##(4) start zero:
/usr/bin/python3.9 $ZeroScript "${SITE[@]}" &

##(5) start server:
/usr/bin/python3.9 $ServerScript "${SITE[@]}" "${SNPortPair[0]}" "${ENVIDASPORT[@]}" "${SITE[@]}" "${SNPortPair[2]}" "${ENVIDASPORT[@]}" & 

##(6) start button
#/usr/bin/python3.9 $ButtonScript &

##(7) start periodic_restart:
/usr/bin/python3.9 $RestartScript &

##(8) start RPMScript:
/usr/bin/python3.9 $RPMScript &

##(9) start HeaterScript:
/usr/bin/python3.9 $HeaterScript &

##(10) start NTPScipt:
/usr/bin/python3.9 $NTPScript &

##(11) start RebootSensor
/usr/bin/python3.9 $RebootSensor