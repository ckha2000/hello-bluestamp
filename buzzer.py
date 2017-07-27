import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)


def buzz(pitch, duration):
    period = 1.0/pitch
    delay = period/2
    cycles = int(duration*pitch)
    for i in range(cycles):
        GPIO.output(26, True)
        time.sleep(delay)
        GPIO.output(26, False)
        time.sleep(delay)

#buzz(10, 0.5)     -test buzzer
