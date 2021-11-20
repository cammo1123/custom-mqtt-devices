import requests, json, os, time, globalVars

filename = os.path.basename(__file__)



def clearConsole():
    command = 'clear'
    if os.name in ('nt', 'dos'):  # If Machine is running on Windows, use cls
        command = 'cls'
    os.system(command)

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
		self.out_temp = 0
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
		if (time.time() >= self.lastTime + 60):
			self.lastTime = time.time()
			self.update()
		else: 
			return
	
	def update(self):	
		url = "http://cloud.linked-go.com:84/cloudservice/api/app/device/getDataByCode.json"
		myobj = {"device_code":"34EAE797DEF6", "protocal_codes": [        
			"Power", 	# Power
			"Mode", 	# Mode Temp
		# "Manual-mute", 
			"T02", 		# In Temp
			"2074",		# Flow Sensor
		# "2075",
		# "2076",
		# "2077",
		# "H03",
			"Set_Temp",	# Target Temp
		# "R08",
		# "R09",
		# "R10",
		# "R11",
		# "R01",
		# "R02",
		# "R03",		# Mirror Target Temp
		# "T03", 		# Out Temp
		# "1158",
		# "1159",
		# "F17",
		# "H02",
		# "2064"
	   ]}
		x = requests.post(url, json = myobj, headers = self.headers)

		if (x.status_code == 200):
			res = json.loads(x.text)

			self.mode = self.modes[int([item for item in res["object_result"] if item.get('code') == "Mode"][0]["value"])]
			self.power = int([item for item in res["object_result"] if item.get('code') == "Power"][0]["value"])
			self.flow = int([item for item in res["object_result"] if item.get('code') == "2074"][0]["value"], 2)

			if (self.power == 0 or self.flow != 0):
				self.mode = "off"

			self.temp = float([item for item in res["object_result"] if item.get('code') == "T02"][0]["value"])
			self.set_temp = float([item for item in res["object_result"] if item.get('code') == "Set_Temp"][0]["value"])

			self.update_status()
		
		elif (x.status_code == 401):
			self.login()
		
		else:
			print(x.status_code)

	def update_status(self):
		status = {
			"mode": self.mode,
			"temp": self.temp,
			"set_temp": self.set_temp
		}
		self.client.publish(f"homeassistant/climate/{self.channel}/status", json.dumps(status))


	def on_message(self, client, userdata, mess):
		if (mess.topic == f"homeassistant/climate/{self.channel}/set"):
			message = json.loads(str(mess.payload.decode("utf-8")))

			if "set_temp" in message:
				self.set_temp = float(message["set_temp"])
			if "mode" in message:
				self.mode = message["mode"]
				if (self.mode != "off"):
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
					"device_code": "34EAE797DEF6",
					"protocol_code": "R02",
					"value": f"{int(float(self.set_temp))}"
				},
				{
					"device_code": "34EAE797DEF6",
					"protocol_code": "Set_Temp",
					"value": f"{int(float(self.set_temp))}"
				},
			]
		}

		x = requests.post(url, json = json, headers = self.headers)


	def log(self):
		clearConsole()
		print(f"==== Stats at {time.strftime('%H:%M:%S', time.localtime())} ====")
		print(f"Mode: {self.mode}")
		print(f"Temp: {self.temp}")
		print(f"Set Temp: {self.set_temp}")