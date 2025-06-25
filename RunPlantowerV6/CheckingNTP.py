import ntplib
from datetime import datetime
import subprocess
import time

def get_ntp_time(server="10.7.36.122"):
    try:
        client = ntplib.NTPClient()
        response = client.request(server, version=3)
        ntp_time = datetime.fromtimestamp(response.tx_time)
        #print(f"Time from NTP server ({server}): {ntp_time}")

        # Format the time string for the `date` command: "MMDDhhmmYYYY.ss"
        time_str = ntp_time.strftime('%m%d%H%M%Y.%S')

        # Use the `date` command to set the system time
        subprocess.run(['sudo', 'date', time_str], check=True)
       # print("System time updated successfully.")
        
        return ntp_time
    except Exception as e:
        #print(f"Failed to get or set time from NTP server: {e}")
        return None

if __name__ == "__main__":
    while True:
        get_ntp_time("10.7.36.122")  # Replace with your NTP server
        #print("Sleeping for 4 hours...\n")
        time.sleep(4 * 60 * 60)  # 4 hours in seconds
