#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import LCD1602
import ADC0834
import time
import math

LED_PIN = 25
FAIL_FLAG = False


def init():
	setup_gpio()
	setup_adc0834()
	setup_lcd1602()

def setup_lcd1602():
	LCD1602.init(0x27, 1)	# init(slave address, background light)
	LCD1602.write(0, 0, 'Greetings!')
	LCD1602.write(1, 1, 'From SunFounder')
	time.sleep(2)

def setup_gpio():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.HIGH)

def setup_adc0834():
	ADC0834.setup()



def loop():
	while True:
		try:
			cel, fah = get_temp_val()
		except ValueError as e:
			time.sleep(0.5)
			continue
		print ('Celsius: %.2f C  Fahrenheit: %.2f F' % (cel, fah))
		time.sleep(2) # takes samples each 2 sec


def get_temp_val() -> tuple[float, float]:
	analogVal = ADC0834.getResult()
	print(analogVal)
	if not analogVal: # temperature mesure is 0, something is wrong
		blink_led(LED_PIN) # blink red led
		print('unable to sample temperature')
		raise ValueError
	else:
		Vr = 5 * float(analogVal) / 255
		Rt = 10000 * Vr / (5 - Vr)
		temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15+25)))
		temp_c = convert_to_c(temp)
		temp_f = convert_to_f(temp)
		return temp_c, temp_f


def convert_to_c(val: float) -> float:
	return val - 273.15


def convert_to_f(val: float) -> float:
	return convert_to_c(val) * 1.8 + 32


def blink_led(led_pin: int):
	GPIO.output(led_pin, GPIO.LOW) # turn on
	time.sleep(1)
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