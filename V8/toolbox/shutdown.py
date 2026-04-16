import subprocess
import time

import CheckOperationVersion1v3 as CheckOP

# Alert operator that shutdown was requested
CheckOP.AlertOPpause(1)

time.sleep(2)

# Final shutdown alert
CheckOP.AlertOPpause(5)

# Shutdown system
subprocess.run(['sudo', 'shutdown', 'now'])