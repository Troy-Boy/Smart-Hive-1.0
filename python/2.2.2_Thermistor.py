#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import ADC0834
import time
import math

LED_PIN = 25
FAIL_FLAG = False


def init():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.HIGH)
	ADC0834.setup()

def loop():
	while True:
		analogVal = ADC0834.getResult()
		Vr = 5 * float(analogVal) / 255
		Rt = 10000 * Vr / (5 - Vr)
		print(Rt)
		if not Rt:
			FAIL_FLAG = False
			blink_led()
			print('Unable to get temperature')
		else:
			temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15+25)))
			Cel = temp - 273.15
			Fah = Cel * 1.8 + 32
			print ('Celsius: %.2f C  Fahrenheit: %.2f F' % (Cel, Fah))
			time.sleep(2)

def blink_led(led_pin: int):
	for _ in range(3):
		GPIO.output(led_pin, GPIO.LOW) # turn on
		time.sleep(0.5)
		GPIO.output(led_pin, GPIO.HIGH) # turn off led

def destroy():
	GPIO.cleanup()
	ADC0834.destroy()


if __name__ == '__main__':
	init()
	try:
		loop()
	except KeyboardInterrupt:
		destroy()