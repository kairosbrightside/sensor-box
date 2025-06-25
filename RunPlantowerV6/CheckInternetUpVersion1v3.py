#Checks if internet is up and restarts if needed
#run from crontab 1-per day

#libraries
import subprocess
import datetime, time

import CheckOperationVersion1v3 as CheckOP

#check that we can see the modem gateway
ip2ping = '192.168.13.101' #change this to ping WAN
#ip2ping = '192.168.1.1' #change this to ping WAN
LANip2ping = ip2ping

#main
if(__name__ == '__main__'):
    
    while True:
        #1 min pause
        time.sleep(60)
        #check modem connection at 8 in the morning every day:
        if ((datetime.datetime.now().minute >= 0) &  (datetime.datetime.now().minute < 1)):

            PacketLoss = CheckOP.CheckInternet(ip2ping)
            
            #(0)wan vs lan
            if(PacketLoss > 0.5):
                
                PacketLoss = CheckOP.CheckInternet(LANip2ping)
                #EB - "diff WAN and LAN networks"
                #use this condition if you can see the modem gateway but not the internet/DEQ network
                
            #(1)Try again for 15 min.
            if(PacketLoss > 0.5):
                for ind in range(15):
                    time.sleep(60)
                    PacketLoss = CheckOP.CheckInternet(ip2ping)
                    
                    if (PacketLoss == 0):
                        break
                    
            #(2)Reset the network connection
            if(PacketLoss > 0.5):
                try:
                    subprocess.run(['systemctl', 'restart', 'networking'])
                except:
                    pass
                
                #wait 15 min.
                time.sleep(15*60)
                PacketLoss = CheckOP.CheckInternet(ip2ping)
                
            #(3)Try again for 15 min.
            if(PacketLoss > 0.5):
                for ind in range(15):
                    time.sleep(60)
                    PacketLoss = CheckOP.CheckInternet(ip2ping)
                    
                    if (PacketLoss == 0):
                        break
                    
            #(4) reboot the RPi
            if(PacketLoss > 0.5):
                subprocess.run(['sudo', 'reboot', 'now'])

