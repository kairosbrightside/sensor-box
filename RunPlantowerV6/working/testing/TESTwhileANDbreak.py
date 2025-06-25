
import time

InternetUp = 0
FailedConnection = 0
nTry = 10

while(InternetUp == 0):
    
    PacketLoss = 1
    
    time.sleep(1) 
        
    if(PacketLoss == 0):
        InternetUp = 1
    else:
        InternetUp = 0
        FailedConnection += 1
        
    print(FailedConnection)
    #shutdown if we could not establish a connection
    if(FailedConnection >= nTry):
        print('Hitting break')
        break


print(InternetUp)
print(FailedConnection)