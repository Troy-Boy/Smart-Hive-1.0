'''
**********************************************************************
* Filename    : dht11.py
* Description : test for SunFoudner DHT11 humiture & temperature module
* Author      : sunfounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Dream    2016-09-30    New release
**********************************************************************
'''
#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import LCD1602


dhtPin = 13

GPIO.setmode(GPIO.BCM)

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def read_dht11():
	GPIO.setup(dhtPin, GPIO.OUT)
	GPIO.output(dhtPin, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(dhtPin, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(dhtPin, GPIO.IN, GPIO.PUD_UP)

	unchanged_count = 0
	last = -1
	data = []
	lengths = []
	current_length = 0

	# acquire input
	while unchanged_count < MAX_UNCHANGE_COUNT:
		current = GPIO.input(dhtPin)
		data.append(current)
		if last != current:
			unchanged_count = 0
			last = current
		else:
			unchanged_count += 1

	state = STATE_INIT_PULL_DOWN
	
	# wtf 
	for current in data:
		current_length += 1

		if state == STATE_INIT_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_INIT_PULL_UP
		elif state == STATE_INIT_PULL_UP:
			if current == GPIO.HIGH:
				state = STATE_DATA_FIRST_PULL_DOWN
		elif state == STATE_DATA_FIRST_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_DATA_PULL_UP
		elif state == STATE_DATA_PULL_UP:
			if current == GPIO.HIGH:
				current_length = 0
				state = STATE_DATA_PULL_DOWN
		elif state == STATE_DATA_PULL_DOWN:
			if current == GPIO.LOW:
				lengths.append(current_length)
				state = STATE_DATA_PULL_UP
		else: 
			continue

	if len(lengths) != 40:
		return ()

	shortest_pull_up = min(lengths)
	longest_pull_up = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	# convert to byte
	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
	for i in range(0, len(bits)):
		byte = byte << 1
		byte = byte | 1 if bits[i] else byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0

	# check if transmission is ok
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		return ()

	return the_bytes[0], the_bytes[2]

def setup_lcd1602():
	LCD1602.init(0x27, 1)	# init(slave address, background light)
	LCD1602.write(0, 0, 'HelloWorld!')
	LCD1602.write(1, 1, 'Welcom to SmartHive')
	time.sleep(2)

def main():
	setup_lcd1602()	
	while True:
		result = read_dht11()
		if result:
			humidity, temperature = result
		LCD1602.clear()
		LCD1602.write(0, 0, f'Humidity: {humidity}%')
		LCD1602.write(0, 1, f'Temperature: {temperature} C')
		time.sleep(2) # takes samples each 2 sec
		LCD1602.clear()


def destroy():
	GPIO.cleanup()


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		destroy() 