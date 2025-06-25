
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)

GPIO.output(21, GPIO.HIGH)
GPIO.input(21)
GPIO.output(21, GPIO.LOW)
GPIO.input(21)



