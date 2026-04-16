import subprocess, time, datetime

DAY = "Tuesday"
HOUR = 10
MIN = 10

last = None

while True:
    time.sleep(30)

    now = datetime.datetime.now()
    key = (now.strftime("%A"), now.hour, now.minute)

    if key == (DAY, HOUR, MIN) and key != last:
        subprocess.run(['sudo', 'reboot', 'now'])
        last = key