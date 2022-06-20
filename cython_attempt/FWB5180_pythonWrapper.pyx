cimport c_FWB5180

def open_connection():
	print('attempting to open device')
	devID = c_FWB5180.openUSB5100()
	print('opened device!')
	
	print(devID)
	return devID

