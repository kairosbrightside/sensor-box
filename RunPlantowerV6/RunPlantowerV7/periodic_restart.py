#reboot the raspberry pi at specified interval

#libraries
import subprocess
import datetime, time

# specify restart interval
reboot_day = "Tuesday" # what day of the week do we want a reboot
reboot_hour = 10       # am
reboot_min = 10         # minutes into the hour

#main 
if(__name__ == '__main__'):
    
    while True:
        
        time.sleep(60) #1 min pause
        
        i_ddd = datetime.datetime.today().strftime("%A")
        i_hour = datetime.datetime.now().hour
        i_min = datetime.datetime.now().minute
         
        if((i_ddd == reboot_day) & (i_hour == reboot_hour) & (i_min == reboot_min)):
            subprocess.run(['sudo', 'reboot', 'now'])

