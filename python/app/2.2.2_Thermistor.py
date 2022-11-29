#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time
import math
import LCD1602
import ADC0834


LED_PIN = 25
DHT_PIN = 13
FAIL_FLAG = False

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5


def init():
	"""Initialize pins and connected IO."""
	setup_gpio() # setup pin mode
	setup_dht() # initialize pin for dht
	setup_adc0834() # initialize pin for dht
	setup_lcd1602() # initialize pin for dht


def setup_dht():
	GPIO.setup(DHT_PIN, GPIO.OUT)


def setup_lcd1602():
	LCD1602.init(0x27, 1)	# init(slave address, background light)
	LCD1602.write(0, 0, 'Greetings!')
	LCD1602.write(1, 1, 'Welcom to SmartHive')
	time.sleep(2)


def setup_gpio():
	GPIO.setmode(GPIO.BCM)
	# GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.HIGH)


def setup_adc0834():
	ADC0834.setup()


def loop():
	deg_sign = u'\N{DEGREE SIGN}'
	while True:
		try:
			hum, temp = get_dht_data()
			print(f'Humidity: {hum}%, Temp: {temp}{deg_sign}C')
			cel, fah = get_temp_val()
		except ValueError as e:
			time.sleep(0.5)
			continue
		# print ('Celsius: %.2f C  Fahrenheit: %.2f F' % (cel, fah))
		LCD1602.clear()
		LCD1602.write(0, 0, f'{cel:.2f}'+'\u0B00'+'C')
		LCD1602.write(0, 1, f'{fah:.2f}'+'\u0B00'+'f')
		time.sleep(2) # takes samples each 2 sec
		LCD1602.clear()


def get_dht_data() -> tuple[list, list]:
	GPIO.output(DHT_PIN, GPIO.HIGH)
	time.sleep(0.1)
	GPIO.output(DHT_PIN, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(DHT_PIN, GPIO.IN, GPIO.PUD_UP)
	unchanged_count = 0
	last = -1
	data = []
	state = STATE_INIT_PULL_DOWN
	lengths = []
	current_length = 0
	
	while True:
		current = GPIO.input(DHT_PIN)
		data.append(current)
		if last != current:
			unchanged_count = 0
			last = current
		else:
			unchanged_count += 1
			if unchanged_count > MAX_UNCHANGE_COUNT:
				break


	for current in data:
		current_length += 1

		if state == STATE_INIT_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_INIT_PULL_UP
			else:
				continue
		if state == STATE_INIT_PULL_UP:
			if current == GPIO.HIGH:
				state = STATE_DATA_FIRST_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_FIRST_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_DATA_PULL_UP
			else:
				continue
		if state == STATE_DATA_PULL_UP:
			if current == GPIO.HIGH:
				current_length = 0
				state = STATE_DATA_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_PULL_DOWN:
			if current == GPIO.LOW:
				lengths.append(current_length)
				state = STATE_DATA_PULL_UP
			else:
				continue
	if len(lengths) != 40:
		#print ("Data not good, skip")
		return (None, None)

	shortest_pull_up = min(lengths)
	longest_pull_up = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
	#print ("bits: %s, length: %d" % (bits, len(bits)))
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
	#print (the_bytes)
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		#print ("Data not good, skip")
		return (None, None)

	return the_bytes[0], the_bytes[2]

def get_temp_val() -> tuple[float, float]:
	analogVal = ADC0834.getResult()
	Vr = 5 * float(analogVal) / 255
	if not Vr: # temperature mesure is 0, something is wrong
		blink_led(LED_PIN) # blink red led
		LCD1602.clear()
		LCD1602.write(3, 0, "Unable to sample temp")
		raise ValueError
	else:
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
	# GPIO.output(led_pin, GPIO.LOW) # turn on
	# time.sleep(1)
	# GPIO.output(led_pin, GPIO.HIGH) # turn off led
	pass

def destroy():
	LCD1602.clear()
	GPIO.cleanup()
	ADC0834.destroy()


if __name__ == '__main__':
	init()
	try:
		loop()
	except KeyboardInterrupt:
		destroy()