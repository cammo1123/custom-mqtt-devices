import json, time, random, globalVars
from rpi_ws281x import *

strip = Adafruit_NeoPixel(98, 18, 800000, 10, False, 200, 0)
strip.begin()

colors = {}

class Light:
	def __init__(self, channel, zone, wipeOrder = [], color = [255, 255, 255]):
		self.color = color
		self.client = globalVars.client
		self.zone = zone
		self.state = "on"
		self.wait_until = 0
		self.brightness = 255
		self.synced_iterations = 0
		self.iterations = 0
		self.effect = "none"
		self.prevEffect = ""
		self.channel = channel

		if (wipeOrder == []):
			self.wipeOrder = zone
		else:
			self.wipeOrder = wipeOrder

		colors[self.channel] = Color(self.color[0], self.color[2], self.color[1])

		globalVars.listeners["iterate"].append(self.iterate)
		globalVars.listeners["update"].append(self.update_state)
		globalVars.listeners["message"].append(self.on_message)
		globalVars.listeners["topic"].append((f"homeassistant/light/{self.channel}/set", 0))

		self.update_state()

	def wheel(self, pos):
		bright = self.brightness / 255

		if pos < 85:
			color = [pos * 3, 255 - pos * 3, 0]
		elif pos < 170:
			pos -= 85
			color = [255 - pos * 3, 0, pos * 3]
		else:
			pos -= 170
			color = [0, pos * 3, 255 - pos * 3]

		return Color(int(color[0] * bright), int(color[1] * bright), int(color[2] * bright))


	def on_message(self, client, userdata, mess):
		if (mess.topic == f"homeassistant/light/{self.channel}/set"):
			message = json.loads(str(mess.payload.decode("utf-8")))

			if "color" in message:
				self.color = message["color"]
				colors[self.channel] = Color(self.color[0], self.color[2], self.color[1])
			if "brightness" in message:
				self.brightness = message["brightness"]
			if "state" in message:
				self.state = message["state"]
			if "effect" in message:
				self.effect = message["effect"]

			self.update_state()

	def update_state(self):
		status = {
			"state": self.state,
			"color": self.color,
			"brightness": self.brightness,
			"effect": self.effect
		}

		bright = self.brightness / 255

		if (self.state == "off"):
			colors[self.channel] = Color(0, 0, 0)
			self.effect = "none"
		else:
			colors[self.channel] = Color(int(self.color[0] * bright), int(self.color[2] * bright), int(self.color[1] * bright))
			
		self.client.publish(f"homeassistant/light/{self.channel}/status", json.dumps(status))
		self.update()

	def iterate(self):
		bright = self.brightness / 255

		if (self.effect == "none" and self.prevEffect == self.effect):
			pass

		elif (self.effect == "none" and self.prevEffect != self.effect):
			for pixel in self.zone:
				strip.setPixelColor(pixel, colors[self.channel])

			self.prevEffect = self.effect

		elif (self.iterations > self.wait_until):	
			if (self.effect == "Strobe"):
				gap = self.iterations % 12
				for pixel in self.zone:
					if (gap == 0):
						strip.setPixelColor(pixel, colors[self.channel])
					else:
						strip.setPixelColor(pixel, 0)
				
			elif (self.effect == "Rainbow"):
				for pixel in self.zone:
					strip.setPixelColor(pixel, self.wheel(
					 	(int(pixel * 256 / strip.numPixels()) + int(self.iterations / 2)) & 255))	

			elif (self.effect == "wipe"):
				pos = self.synced_iterations % len(self.wipeOrder)

				if (self.state == "off"):
					pos = (pos * -1) + (len(self.wipeOrder) - 1)

				try:
					for pixel in self.wipeOrder[pos]:
						strip.setPixelColor(pixel, colors[self.channel])
				except TypeError:
					strip.setPixelColor(self.wipeOrder[pos], colors[self.channel])


				if (self.state != "off" and pos >= len(self.wipeOrder) - 1):
					self.effect = "none"
				elif (self.state == "off" and pos <= 0):
					self.effect = "none"
				
			elif (self.effect == "Chase"):
				for pixel in self.zone:
					if (((pixel - self.synced_iterations) % strip.numPixels()) % 3 == 0):
						strip.setPixelColor(pixel, colors[self.channel])
					else:
						strip.setPixelColor(pixel, 0)
				self.wait(20)

			elif (self.effect == "Rainbow Chase"):
				for pixel in self.zone:
					if (((pixel - self.synced_iterations) % strip.numPixels()) % 3 == 0):
						strip.setPixelColor(pixel, self.wheel(
					 		(int(pixel * 256 / strip.numPixels()) + int(self.iterations / 2) & 255)))
					else:
						strip.setPixelColor(pixel, 0)
				self.wait(20)

			elif (self.effect == "Random"):
				for pixel in self.zone:
						strip.setPixelColor(pixel, Color(
							int(random.randint(0, 255) * bright), 
							int(random.randint(0, 255) * bright), 
							int(random.randint(0, 255) * bright)
						))
				self.wait(20)

			elif (self.effect == "Morse"):
				message = [255, 165058, 0, 255, 165058, 255, 0, 255, 255, 255, 255, 0, 165058, 255, 0, 255, 165058]
				mess = message[::-1]

				# .- .-. .... -. .-
				offset = (self.synced_iterations % (len(self.zone) + len(mess)) - len(mess))

				for pixel in self.zone:
					strip.setPixelColor(pixel, 0)

				for pixel in range(len(mess)):
					if (pixel + offset >= 0):
						if (pixel + offset < len(self.zone)):
							try:
								strip.setPixelColor(self.zone[pixel + offset], mess[pixel])
							except:
								strip.setPixelColor(pixel, 0)
				self.wait(20)

			elif (self.effect == "Snake"):
				message = [255, 255, 255]
				mess = message[::-1]

				offset = (self.synced_iterations % (len(self.zone) + len(mess)) - len(mess))

				for pixel in self.zone:
					strip.setPixelColor(pixel, 0)

				for pixel in range(len(mess)):
					if (pixel + offset >= 0):
						if (pixel + offset < len(self.zone)):
							try:
								strip.setPixelColor(self.zone[pixel + offset], colors[self.channel])
							except:
								strip.setPixelColor(pixel, 0)

				self.wait(20)

			elif (self.effect == "Rainbow Snake"):
				snakeLen = 5 

				offset = (self.synced_iterations % (len(self.zone) + snakeLen) - snakeLen)

				for pixel in self.zone:
					strip.setPixelColor(pixel, 0)

				for pixel in range(snakeLen):
					if (pixel + offset >= 0):
						if (pixel + offset < len(self.zone)):
							try:
								strip.setPixelColor(self.zone[pixel + offset], self.wheel(
									(int(self.zone[pixel + offset] * 256 / strip.numPixels()) + int(self.iterations / 2)) & 255))	
							except:
								strip.setPixelColor(pixel, 0)
				self.wait(20)			

			self.synced_iterations = self.synced_iterations + 1

		self.iterations = self.iterations + 1

	def wait(self, wait_iterations):
		self.wait_until = self.iterations + wait_iterations

	def update(self):
		if (self.effect == "none"):
			self.synced_iterations = 0
			self.wait_until = 0
			self.effect = "wipe"

def show():
	strip.show()

# def on_message(client, userdata, message):
# 	if (message.topic == "homeassistant/status"):
# 		for i in range(len(listeners["update"])):
# 			listeners["update"][i]()
# 	else:
# 		for i in range(len(listeners["message"])):
# 			listeners["message"][i](client, userdata, message)

# def on_connect(client, userdata, message, _):
# 	for i in range(len(listeners["update"])):
# 		listeners["update"][i]()

# client.subscribe(listeners["topic"])
# client.on_connect = on_connect
# client.on_message = on_message

# while True:
# 	mainLight.iterate(iterations)
# 	bedLight.iterate(iterations)
# 	desklight.iterate(iterations)

# 	strip.show()

# 	iterations = iterations + 1
# 	client.loop(0.005)