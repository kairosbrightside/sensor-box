import subprocess, time, os

def processes_running():
    ps = subprocess.check_output(['ps', '-ef']).decode()

    required = [
        "main_logger.py",
        "zero_control.py",
        "RPM"
    ]

    return all(r in ps for r in required)


def data_updating(path):
    try:
        return (time.time() - os.path.getmtime(path)) < 120
    except:
        return False


while True:
    if not processes_running():
        print("Process failure → restart")
        subprocess.run(['systemctl', 'restart', 'runPMshell'])
    
    if not data_updating("particle_log.csv"):
        print("Data stale → restart")
        subprocess.run(['systemctl', 'restart', 'runPMshell'])

    time.sleep(60)