import RPi.GPIO as GPIO
import os
import time
import datetime

pinNum = 12

GPIO.setmode(GPIO.BCM)
GPIO.setup(pinNum,GPIO.IN, pull_up_down=GPIO.PUD_UP)

prev_input = True

def readMessage():    
  date = time.strftime("%A %B %d %Y", time.localtime())    
  date_message = "Today is " + date
  print(date_message)

while True:
    input_state = GPIO.input(pinNum)
    
    if (not input_state):
        readMessage()
        time.sleep(0.2)

    prev_input = input_state
