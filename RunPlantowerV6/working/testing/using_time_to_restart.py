#reboot the raspberry pi at specified interval

#libraries
import subprocess
import datetime, time

# specify restart interval
reboot_day = "Friday" # what day of the week do we want a reboot
reboot_hour = 11       # am
reboot_min = 50         # minutes into the hour

#main 
if(__name__ == '__main__'):
    
    while True:
        
        time.sleep(5) #5 sec pause
        
        i_ddd = datetime.datetime.today().strftime("%A")
        i_hour = datetime.datetime.now().hour
        i_min = datetime.datetime.now().minute
        
        print(i_ddd)
        print(i_hour)
        print(i_min)
        
        if((i_ddd == reboot_day) & (i_hour == reboot_hour) & (i_min == reboot_min)):
            subprocess.run(['sudo', 'reboot', 'now'])