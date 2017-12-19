""" Python code to get sensor data through Raspberry Pi GPIO and send it to AWS IoT through the MQTT protocol over secure connection"""

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import datetime

#Function returns current temperature when called
def getTemperature():
	import spidev
	from time import sleep


	# First open up SPI bus
	spi = spidev.SpiDev()
	spi.open(0, 0)

	# Initialize what sensor is where
	tempChannel = 1


	def getReading(channel):
		# First pull the raw data from the chip
		rawData = spi.xfer([1, (8 + channel) &lt;&lt; 4, 0])
		# Process the raw data into something we understand.
		processedData = ((rawData[1] &amp; 3) &lt;&lt; 8) + rawData[2]
		return processedData

	def convertTemp(bitValue, decimalPlaces=2):
		# Converts to degrees Celsius
		temperature = ((bitValue * 330) / float(1023))
		# 3300 mV / (10 mV/deg C) = 330
		temperature = round(temperature, decimalPlaces)
		return temperature

	
	tempData = getReading(tempChannel)	
	temperature = convertTemp(tempData)
	return temperature

def send_to_AWS():
	# Publish sensor data values in a loop forever
	from gpiozero import LightSensor
	ldr = LightSensor(4)
	loopcount = 0
	while True:
		ldr_d = ldr.value
		temperature = getTemperature()
		msg = '"LDR_value":"{}","Temperature":"{}"'.format(ldr_d,temperature)
		msg = '{'+msg+'}'
		myAWSIoTMQTTClient.publish(topic,msg,1)
		time.sleep(20)


def MQTT_connect():
	# Read in command-line parameters
	parser = argparse.ArgumentParser()
	parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
	parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
	parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
	parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
	parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
						help="Use MQTT over WebSocket")
	parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
						help="Targeted client id")
	parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")


	args = parser.parse_args()
	host = args.host
	rootCAPath = args.rootCAPath
	certificatePath = args.certificatePath
	privateKeyPath = args.privateKeyPath
	useWebsocket = args.useWebsocket
	clientId = args.clientId
	topic = args.topic

	# Configure logging
	logger = logging.getLogger("AWSIoTPythonSDK.core")
	logger.setLevel(logging.DEBUG)
	streamHandler = logging.StreamHandler()
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	streamHandler.setFormatter(formatter)
	logger.addHandler(streamHandler)

	# Init AWSIoTMQTTClient
	myAWSIoTMQTTClient = None
	myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
	myAWSIoTMQTTClient.configureEndpoint(host, 8883)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

	# AWSIoTMQTTClient connection configuration
	myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
	myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
	myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
	myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
	myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

	# Connect and subscribe to AWS IoT
	myAWSIoTMQTTClient.connect()
	myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
	time.sleep(2)

	Send_to_AWS()
		
#main function call	
MQTT_connect()