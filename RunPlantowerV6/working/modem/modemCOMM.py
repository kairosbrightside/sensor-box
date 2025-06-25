
import serial
import time
lcmodem = serial.Serial("/dev/ttyACM0", baudrate=9600,timeout=1.0)
#lcmodem = serial.Serial("/dev/ttyAMA0", baudrate=9600,timeout=1.0)

def Qmodem(ATcommand):
    ATcommand = ATcommand + '\r\n'
    AT2send = ATcommand.encode('utf-8')
    lcmodem.write(AT2send)
    out = lcmodem.readall()
    out = out.decode('utf-8')
    out = out.split('\r\n')
    return(out)

#ModSpeak = Qmodem('ATE')
#print(ModSpeak)
#time.sleep(1)

#ModSpeak = Qmodem('ATI')
#print(ModSpeak)
#time.sleep(1)

#ModSpeak = Qmodem('AT+CIFSR')
#print(ModSpeak)
#time.sleep(1)

#
ModSpeak = Qmodem('AT+CGDCONT?')
print(ModSpeak)
time.sleep(1)
#
ModSpeak = Qmodem('AT^SIMONI')
print(ModSpeak)
time.sleep(1)

#verbose error
#ModSpeak = Qmodem('AT+CMEE=2')
#print(ModSpeak)
#time.sleep(1)

#restart modem
#ModSpeak = Qmodem('AT=CFUN=4,1')
#print(ModSpeak)
#time.sleep(1)