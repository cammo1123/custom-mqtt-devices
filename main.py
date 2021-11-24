#!/usr/bin/python3

import aquaTemp, lightStrip, globalVars

if (__name__ == "__main__"):
	globalVars.init()

	# ========= Device Setup and Configuration ========= #
	heater = aquaTemp.Heater("pool_heater")
	mainLight = lightStrip.Light("mainlight", [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94], [[64, 63], [65, 62], [66, 61], [67, 60], [68, 59], [69, 58], [70, 57], [71, 56], [72, 55], [73, 54], [74, 53], [75, 52], [76, 51], [77, 50], [78, 49], [79, 48], [80, 47], [81, 46], [82, 45], [83, 44], [84, 43], [85, 42], [86, 41], [87, 40], [88, 39], [89, 38], [90, 37], [91, 36], [92, 35], [93, 34], [94, 33], 32, 31, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
	bedLight = lightStrip.Light("bedlight", [ 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30 ])
	desklight = lightStrip.Light("desklight", [ 95, 96 ])


	# ========= Correctly allocate MQTT events ========= #
	globalVars.client.subscribe(globalVars.listeners["topic"])

	# ========= Main Program Loop ========= #
	while True:
		globalVars.iterate()
		