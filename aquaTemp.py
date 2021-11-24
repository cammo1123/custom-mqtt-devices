import requests, json, os, time, globalVars

filename = os.path.basename(__file__)

device_code = "34EAE797DEF6"
INTERVAL = 60

class Heater:
	def __init__(self, channel):
		self.channel = channel
		self.client = globalVars.client		
		self.headers = {}
		self.modes = ["cool", "heat", "auto", "off"]

		self.lastTime = 0
		self.power = 0
		self.mode = 0
		self.flow = 0
		self.temp = 0
		self.ambient_temp = 0
		self.set_temp = 0

		globalVars.listeners["update"].append(self.update)
		globalVars.listeners["message"].append(self.on_message)
		globalVars.listeners["iterate"].append(self.iterate)
		globalVars.listeners["topic"].append((f"homeassistant/climate/{self.channel}/set", 0))

		self.login()

	def login(self):
		print(f"{filename} - Authenticating...")
		url = "http://cloud.linked-go.com:84/cloudservice/api/app/user/login.json"

		myobj = {
			"code": "",
			"login_source": "Android",
			"password": "9070d302c88d39ea2b85c46cf8215aaa",
			"type": "2",
			"user_name": "cammoyouell@gmail.com",
		}

		x = requests.post(url, json = myobj)
		res = json.loads(x.text)

		self.headers["x-token"] = res["object_result"]["x-token"]
		
		print(f"{filename} - Got X-Token: {self.headers['x-token']}")

		self.iterate()
	
	def iterate(self):
		if (time.time() >= self.lastTime + INTERVAL):
			self.lastTime = time.time()
			self.update()
		else: 
			return
	
	def update(self):	
		url = "http://cloud.linked-go.com:84/cloudservice/api/app/device/getDataByCode.json"
		myobj = {
			"device_code": device_code,
			"protocal_codes": [        
				"Power", 	# Power
				"Mode", 	# Mode Temp
				"T02", 		# In Temp
				"T05",		# Ambient Temp
				"2074",		# Flow Sensor
				"Set_Temp",	# Target Temp
			],
	   }

		try:
			x = requests.post(url, json = myobj, headers = self.headers)
		except ConnectionError:
			print(f"{filename} - ConnectionError")

		if (x.status_code == 200):
			res = json.loads(x.text)

			self.mode = int([item for item in res["object_result"] if item.get('code') == "Mode"][0]["value"])
			self.power = int([item for item in res["object_result"] if item.get('code') == "Power"][0]["value"])
			self.flow = int([item for item in res["object_result"] if item.get('code') == "2074"][0]["value"], 2)

			self.temp = float([item for item in res["object_result"] if item.get('code') == "T02"][0]["value"])
			self.set_temp = float([item for item in res["object_result"] if item.get('code') == "Set_Temp"][0]["value"])
			self.ambient_temp = float([item for item in res["object_result"] if item.get('code') == "T05"][0]["value"])

			self.update_status()
		
		elif (x.status_code == 401):
			self.login()
		
		else:
			print(x.status_code)

	def update_status(self):
		if (self.power == 0 or self.flow != 0):
			mode = "off"
		else:
			mode = self.modes[self.mode]

		status = {
			"mode": mode,
			"temp": self.temp,
			"set_temp": self.set_temp
		}

		self.client.publish(f"homeassistant/climate/{self.channel}/status", json.dumps(status))
		self.client.publish(f"homeassistant/sensor/{self.channel}/temperature", self.ambient_temp)


	def on_message(self, client, userdata, mess):
		if (mess.topic == f"homeassistant/climate/{self.channel}/set"):
			message = json.loads(str(mess.payload.decode("utf-8")))

			if "set_temp" in message:
				self.set_temp = float(message["set_temp"])
			if "mode" in message:
				new_mode = self.modes.index(message["mode"])
				
				if (new_mode != 3):
					self.mode = new_mode
					self.power = 1
				else:
					self.power = 0

			self.update_status()
			self.push_to_pump()

	def push_to_pump(self):
		url = "http://cloud.linked-go.com:84/cloudservice/api/app/device/control.json"
		json = {
			"param": [
				{
					"device_code": device_code,
					"protocol_code": "R02",
					"value": f"{int(float(self.set_temp))}"
				},
				{
					"device_code": device_code,
					"protocol_code": "Set_Temp",
					"value": f"{int(float(self.set_temp))}"
				},
				{
					"device_code": device_code,
					"protocol_code": "Mode",
					"value": f"{int(float(self.mode))}"
				},
				{
					"device_code": device_code,
					"protocol_code": "Power",
					"value": f"{int(float(self.power))}"
				},
			]
		}

		try:
			x = requests.post(url, json = json, headers = self.headers)
		except ConnectionError:
			print(f"{filename} - ConnectionError")


	def log(self):
		print(f"==== Data as of {time.strftime('%H:%M:%S', time.localtime())} for device: {device_code} ====")
		print(f"Channel: {self.channel}")
		print(f"Headers: {self.headers}")
		print(f"Power: {self.power}")
		print(f"Mode: {self.mode}")
		print(f"Flow: {self.flow}")
		print(f"Set Temp: {self.set_temp}")
		print(f"Temp: {self.temp}")
		print(f"Ambient: {self.ambient_temp}")