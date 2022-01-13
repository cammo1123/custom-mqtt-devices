import json, time, random, globalVars
from rpi_ws281x import *

NUM_PIXELS = 98

strip = Adafruit_NeoPixel(NUM_PIXELS, 18, brightness = 200)
strip.begin()

colors = {}

class Light:
	def __init__(self, channel, zone, wipeOrder = [], color = [255, 255, 255], effect = "none", test = False):
		self.color = color
		self.client = globalVars.client
		self.zone = zone
		self.state = "on"
		self.wait_until = 0
		self.brightness = 255
		self.synced_iterations = 0
		self.iterations = 0
		self.effect = effect
		self.channel = channel

		self.effects = {
			"Full Cycle": self.fullCycle,
			"Rainbow Snake": self.rainbowSnake,
			"Police": self.police,
			"Snake": self.snake,
			"Morse": self.morse,
			"Rainbow Chase": self.rainbowChase,
			"Random": self.random,
			"Christmas": self.christmas,
			"Chase": self.chase,
			"wipe": self.wipe,
			"Rainbow": self.rainbow,
			"Strobe": self.strobe,
		}

		self.test = test
		self.testMode = 0
		self.testTime = 0

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

		return color

	def setColor(self, pixel, color = None):
		bright = self.brightness / 255	

		if (color == None):
			color = self.color
		strip.setPixelColor(pixel, Color(int(color[0] * bright), int(color[2] * bright), int(color[1] * bright)))

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

			bright = self.brightness / 255	
			if (self.state == "off"):
				colors[self.channel] = Color(0, 0, 0)
				self.effect = "none"
			else:
				colors[self.channel] = Color(int(self.color[0] * bright), int(self.color[2] * bright), int(self.color[1] * bright))

			self.update_state()

	def update_state(self):
		status = {"state": self.state, "color": self.color,	"brightness": self.brightness, "effect": self.effect}
		self.client.publish(f"homeassistant/light/{self.channel}/status", json.dumps(status))
		self.update()

	def wait(self, wait_iterations):
		self.wait_until = self.iterations + wait_iterations

	def update(self):
		if (self.effect == "none"):
			self.synced_iterations = 0
			self.wait_until = 0
			self.effect = "wipe"

	def iterate(self):
		if (self.test == True):
			if (self.iterations % 1000 <= 0):
				self.testTime = time.time_ns()
				self.effect = list(self.effects)[self.testMode]
				self.testMode = (self.testMode + 1) % len(self.effects)
			elif (self.iterations % 1000 >= 999):
				print(f"{self.effect}\n  - {round(1 / (((time.time_ns() - self.testTime) / 1000)/ 1e+9), 2)}fps\n")


		self.iterations = self.iterations + 1

		if (self.iterations > self.wait_until and self.effect != "none"):	
			try:
				self.effects[self.effect]()
										
				self.synced_iterations = self.synced_iterations + 1
				globalVars.updateLight = True
			except KeyError:
				print(f"ERROR: No Effect - {self.effect}")

	def random(self):
		bright = self.brightness / 255	

		for pixel in self.zone:
			self.setColor(pixel, [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])
		self.wait(20)

	def police(self):
		if (self.iterations % 40 < 20):
			for pixel in self.zone:
				self.setColor(pixel, [255, 0, 0])
		else:
			for pixel in self.zone:
				self.setColor(pixel, [0, 0, 255])	

	def strobe(self):
		if (self.iterations % 8 == 0):
			for pixel in self.zone:
				self.setColor(pixel)
		else:
			for pixel in self.zone:
				self.setColor(pixel, [0, 0, 0])

	def rainbow(self):
		for pixel in self.zone:
				self.setColor(pixel, self.wheel(
					(int(pixel * 256 / (strip.numPixels() / 2)) - int(self.iterations / 2)) & 255))	

	def fullCycle(self):
		color = self.wheel(int(self.iterations / 2) & 255)
		
		for pixel in self.zone:
			self.setColor(pixel, color)

	def wipe(self):
		pos = self.synced_iterations % len(self.wipeOrder)
		color = self.color

		if (self.state == "off"):
			pos = (pos * -1) + (len(self.wipeOrder) - 1)
			color = [0, 0, 0]

		try:
			for pixel in self.wipeOrder[pos]:
				self.setColor(pixel, color)
		except TypeError:
			self.setColor(self.wipeOrder[pos], color)


		if (self.state != "off" and pos >= len(self.wipeOrder) - 1):
			self.effect = "none"
		elif (self.state == "off" and pos <= 0):
			self.effect = "none"		

	def chase(self):
		for pixel in self.zone:
			if (((pixel - self.synced_iterations) % strip.numPixels()) % 3 == 0):
				self.setColor(pixel)
			else:
				self.setColor(pixel, [0, 0, 0])

		self.wait(20)	

	def rainbowChase(self):
		for pixel in self.zone:
			if (((pixel - self.synced_iterations) % strip.numPixels()) % 3 == 0):
				self.setColor(pixel, self.wheel(
					(int(pixel * 256 / (strip.numPixels() / 2)) - int(self.iterations / 2) & 255)))
			else:
				self.setColor(pixel, [0, 0, 0])

		self.wait(20)

	def morse(self):
		morse_l = [255, 0, 255]
		morse_s = [0, 255, 255]
		morse_n = [0, 0, 0]
		
		message = [morse_s, morse_s, morse_l, morse_n, morse_s, morse_n, morse_l, morse_l, morse_l, morse_n, morse_s, morse_l, morse_s, morse_n, morse_l, morse_l, morse_s, morse_n, morse_s, morse_s, morse_n, morse_s]

		offset = self.synced_iterations % len(self.zone)

		for i in range(len(self.zone)):
			pixel = self.zone[(i + offset) % len(self.zone)]
			if i < len(message):
				self.setColor(pixel, message[::-1][i])
			else:
				self.setColor(pixel, [0, 0, 0])
		
		self.wait(20)	

	def snake(self):
		offset = round(self.synced_iterations) % len(self.zone)

		for i in range(len(self.zone)):
			pixel = self.zone[(i + offset) % len(self.zone)]
			if i < 12:
				self.setColor(pixel)
			else:
				self.setColor(pixel, [0, 0, 0])

		self.wait(20)

	def christmas(self):
		for pixel in self.zone:
			if (((pixel - self.synced_iterations) % strip.numPixels()) % 4 <= 1):
				strip.setPixelColor(pixel, Color(255, 0, 0))
			else:
				strip.setPixelColor(pixel, Color(0, 0, 255))

		self.wait(20)

	def rainbowSnake(self):
		offset = round(self.synced_iterations / 15) % len(self.zone)

		for i in range(len(self.zone)):
			pixel = self.zone[(i + offset) % len(self.zone)]
			if i < 12:
				self.setColor(pixel, self.wheel((int(pixel * 256 / strip.numPixels()) - int(self.iterations / 2)) & 255))	
			else:
				self.setColor(pixel, [0, 0, 0])
		

def show():
	if globalVars.updateLight:
		strip.show()
		globalVars.updateLight = False