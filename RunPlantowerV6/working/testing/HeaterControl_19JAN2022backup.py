#---------------------------------------------------------------------------#
#inputs from shell
#---------------------------------------------------------------------------#
#stable ==> here
# DataOutDirectory = "/media/pi/data/PMoutputData/" #output directory
# sensorType = "PMS5003st"

#inputs from shell
#site = str(sys.argv[1])
#sn = str(sys.argv[2])
#site = 'BOX'
# sn = '1'
# SensorData = (DataOutDirectory + site + "_" + sensorType + "_sn" + sn + "_" + "1Min.txt")

######################################### 
#(2) create log
#########################################
HeaterLog = (DataOutDirectory + "Heater_" + "Log.txt")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s:%(levelname)s:%(levelno)s:%(message)s')

file_handler = logging.FileHandler(HeaterLog)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

#---------------------------------------------------------------------------#
#set up GPIO ports
try:
    pinhigh = GPIO.input(13)
except:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(13, GPIO.OUT)

#see if pin works
try:
    GPIO.output(13, GPIO.LOW)
    pinhigh = GPIO.input(13)
    logger.info('Heater pin works.  Force heater off.')
except:
    logger.info('Heater pin error.')
    pinhigh = 0

#---------------------------------------------------------------------------#
# adjust this to control how the heater works

# Average over "n_obs_rh_average" minutes to compare RH with threshold
# this will "smooth out" the heater control

n_obs_rh_average = 5 # how many observations 

# max threshold - heater will turn on above this RH
max_rh_threshold = 50

# max threshold - heater will turn off below this RH
min_rh_threshold = 50
#---------------------------------------------------------------------------#

# initiate RH with 50% relative humiditiy
lst_RH= [50] * (n_obs_rh_average - 1) 

#check rh every minute
while True:
    
    time.sleep(60) 
    
    ifile = SensorData
    
    try:
        with open(ifile, "r") as myfile:
            PtowerDATA = myfile.readlines()[-1] #-1 = last line         
    except: 
        logger.info('No PtowerData to inform heater')
    
    RH_i = PtowerDATA.split(',')[10] # NOTE: this is RH * 10
    RH_i = int(RH_i)/10 #convert to percent units
    # print(RH_i)
    
    # average over several minutes to determine RH threshold - NK 
    lst_RH.append(RH_i) # makes a list of the last 30 values
    if len(lst_RH) == n_obs_rh_average:
        mean_RH = np.mean(np.array(lst_RH))
        lst_RH.remove(lst_RH[0]) #remove the first value and retun the last 29 values
        
    if (mean_RH >= max_rh_threshold) & (pinhigh == False):
        GPIO.output(13, GPIO.HIGH)
        print('pin set high')

        
    if (mean_RH < min_rh_threshold) & (pinhigh == True):
        GPIO.output(13, GPIO.LOW)
 