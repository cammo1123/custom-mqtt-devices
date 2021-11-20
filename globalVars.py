import paho.mqtt.client as mqtt
import lightStrip

def init():
	global listeners
	listeners = {"update": [], "message": [], "iterate": [], "topic": [("homeassistant/status", 0)]}

	mqttBroker ="homeassistant.local"

	global client
	client = mqtt.Client()
	client.connect(mqttBroker)
	client.on_connect = on_connect
	client.on_message = on_message

def on_message(client, userdata, message):
	if (message.topic == "homeassistant/status"):
		for i in range(len(listeners["update"])):
			listeners["update"][i]()
	else:
		for i in range(len(listeners["message"])):
			listeners["message"][i](client, userdata, message)

def on_connect(client, userdata, message, _):
	for i in range(len(listeners["update"])):
		listeners["update"][i]()

def iterate():
	for i in range(len(listeners["iterate"])):
		listeners["iterate"][i]()

	lightStrip.show()
	client.loop(0.005)