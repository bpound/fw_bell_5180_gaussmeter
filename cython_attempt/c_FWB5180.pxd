cdef extern from "FWB5180.h":
	int openUSB5100()
	void closeUSB5100(int devID)
	int scpiCommand(int devID,char* cmd, char* result, int length)