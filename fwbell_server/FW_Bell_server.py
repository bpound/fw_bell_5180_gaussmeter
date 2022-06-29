# FW Bell gaussmeter server
# Purpose: to provide an interface with the gaussmeter.
# History: I could not get the 64 bit DLLs to work, only the 32 bit DLLs, so I wrote this server code that is run in 32 bits, and can be accessed via sockets by either 32 or 64 bit softwares.
# Behavior:
# 1) upon running this program, the code will automatically try to initialize a connection with the probe. 
# -- once the usb connection is found, it will only try once to do the initialization. if it doesn't work then, it won't ever work, so it doesn't make sense to keep trying
# 2) after initializing the connection will be tested with the identity command. 
# 3) The default parameters will also be set.


import socket,ctypes,time,os,usb.core

## settings and global variables
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

# may may need to change this path if you are using a different computer, despite being the default installation directory
# in any case make sure it points to the directory that contains the 32 bit DLLs of usb5100.dll and libusb0.dll
pathDLL_32bit = "C:\\Program Files (x86)\\FW Bell\\PC5180"
pathDLL_64bit = "C:\\Users\\Ben\\Documents\\UCLA\\Research\\Hardware\\fw_bell_magnetic_field_probe\\usb5100-x64\\x64-dist\\64bit\\"

INITIALIZED = False
LENGTH = 80

# default gaussmeter settings
MODE = 'dc-tesla'
RANGEB = 2

# before running you may need to install pyusb module: pip install pyusb

import ctypes,time
import os 
import usb.core 

###########
# some universal defaults go here.
###########

MODE = 'dc-tesla'
RANGEB = 2

# python C:\\Users\\Ben\\Documents\\UCLA\\Research\\Hardware\\fw_bell_magnetic_field_probe\\usb5100-x64\\x64-dist\\fw_bell_py_2.py"

# paths to the 32 and 64 bit DLL files are hardcoded here.
#Note that usb5100.dll and libusb0.dll must be in the same directory
# Recommended to put 32 bit in one folder and 64 bit in another folder
# because for the calling sequence, they must be named as such, but the 64 bit have -x64 appended. To make the libraries work, you need to strip that part.
#pathDLL_32bit = "C:\\Users\\Ben\\Documents\\UCLA\\Research\\Hardware\\fw_bell_magnetic_field_probe\\usb5100-x64\\x64-dist\\32bit\\"
#pathDLL_32bit = "C:\\Windows\\System32\\"
#pathDLL_64bit = "C:\\Users\\Ben\\Documents\\UCLA\\Research\\Hardware\\fw_bell_magnetic_field_probe\\usb5100-x64\\x64-dist\\64bit\\"

class FW_BELL_5180_gaussmeter():
    def __init__(self,length=80):
        """
        Purpose: class to initialize and use the FW Bell 5180 gaussmeter
        Inputs:
        -- mode='dc-tesla',dc-gauss','dc-am','ac-tesla','ac-gauss','ac-am'
        -- rangeB= -1 for auto, 0 (0 - 300 G) low range, 1 (1-3 kG) mid range, or 2 (2-30 kG) high field range. Note that the auto function doesn't seem to work (gets a syntax error), so its probably better to set the range yourself.
        -- length=80, which is the default return string buffer length. 80 is a good numer, only increase this if you start stringing together lots of commands.
        -- checkUSB: use usb.core to see if the device is attached.
        """
        
        # save as defaults, for now.
        self.mode = MODE
        self.rangeB = RANGEB
        self.length = length # this is for the pointers that return statuses. The manual said 80 should be big enough, though I don't think there is much in the way of making a bigger buffer if needed (though I don't think its needed)

        # determines whether being run by 32 or 64 bit python
        if ctypes.sizeof(ctypes.c_void_p) == 4:
            pathDLL = pathDLL_32bit
        else:
            pathDLL = pathDLL_64bit
            print('I hope you have figured out how to make this code work with 64 bit libraries, because I never could make it work. Only 32-bit libraries (with 32 bit python) work current.')
        
        # this makes sure that the dll is found. No need to do anything about the libusb0.dll, the usb5100.dll automatically calls and loads it.
        dllName = os.path.join(pathDLL,"usb5100.dll" )
        fwbell = ctypes.CDLL(dllName)
        
        # define open and close functions with argument and return types.
        self.openUSB5100 = fwbell.openUSB5100 
        self.openUSB5100.argtypes = ()
        self.openUSB5100.restype = ctypes.c_uint
        
        self.closeUSB5100 = fwbell.closeUSB5100
        self.closeUSB5100.argtypes = [ctypes.c_uint]
        self.closeUSB5100.restype = None
        
        self.scpiCommand = fwbell.scpiCommand
        self.scpiCommand.argtypes = [ctypes.c_uint,ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char),ctypes.c_int]
        self.scpiCommand.restype = ctypes.c_int
        
        self.initialized_gaussmeter=False
    def _str_to_b_str(self,cmd):
        """
        Purpose: take a string, normal or byte, and make sure to return a byte string
        
            input: a string (byte or normal)
            output: a byte string
        """

        # check if it is a byte string
        if isinstance(cmd, bytes):
            pass # do nothing if it is a byte string
        else:
            cmd = bytes(cmd,'utf-8') # convert it to a byte string if it is a normal string, and return it.
            
        return cmd    
    def initialize_gaussmeter(self,mode=MODE,rangeB= RANGEB):
        
        # use usb.core to try to find the gaussmeter
        # this is useful because the gaussmeter tends to not be ready for use for several seconds after being plugged in and initialized by windows.
        flag = True
        while 1:
            dev_list = usb.core.show_devices()
            if "DEVICE ID 16a2:5100" not in dev_list and flag: # if you use a different gaussmeter, you will need to change this device ID
                print('trying to find device')
                time.sleep(1)
            else:
                #print(dev_list[:-1])
                #print(len(dev_list))
                print(f'Found the device, moving on.')
                break
         
                
        # open device and save handle to self.idn. should be a 4-bit number, not zero. 
        try:
            idn = self.openUSB5100()
            
            if idn != 0:
                print('initialization successful, id number: ',idn)
                self.initialized_gaussmeter = True
                self.idn = idn 
            else:
                print('initialization failed')
                self.idn = 0
                
        except Exception as e:
            print('initialization failed with error:')
            print(e)
            self.idn = 0

        # test the connection to make sure that it works    
        self.test_connection()
        
    def direct_command(self,cmd):
        """
        Purpose: execute a user-specfied SCPI command. This is called by other helper functions.
        Inputs:
        -- cmd: command string to execute. Can be normal or byte string, this is checked
        -- output: list of ["None","printed", and or "returned"] to do nothing with the output, print to the terminal, or return the value. Can put in a list, i.e. for ['printed','returned'] to do both. 
        Only nomincal slicing of [2:-1] type is done, you may need to do more slicing for your purposes (like stripping the T from the measurement command)
        """
    
        # do a check to make sure that cmd is a byte string, not a string, and do the conversion if necessary
        cmd = self._str_to_b_str(cmd)
        
        #cmd = b"*OPC?;" + cmd
                        
        # now that we have a byte string, try to execute the command
        
        resp= ctypes.create_string_buffer(self.length-1) # it automatically gets terminated by a 0 byte, so we need to create a string buffer with one fewer to account for this.
                        
        # to my knowlegde ret is always returned as 0, no matter what, all messages are returned in the string bugffer "resp".
        ret = self.scpiCommand( self.idn , ctypes.create_string_buffer(cmd) ,resp,self.length )
        string_value = resp.value.decode()
                
        #val = string_value[2:-1]
        val = string_value
            
        return val               
    def test_connection(self):
        """
        Purpose: to test the connection with the gauss probe by sending '*IDN?' and seeing if it will respond appropriately.
        Inputs/Outputs: none
        """
            
        if self.initialized_gaussmeter:
            try:
                print('Attempting to query with the identity command.')
                cmd = b"*IDN?"
                ret_str = self.direct_command(cmd)
                print(f"result: {ret_str}")
                
                if ret_str[:5] == 'error':
                    print('it appears there was an error. See the output.')
                
            except Exception as e:
                print('identity command failed. here is the error message:')
                print(e)
        else:
            print('probe is not initialized; aborting test connection command')    
    def close_connection(self):
        """
        purpose: close connection
        inputs/output: none
        """
    
        if self.initialized_gaussmeter:
            try:
                self.closeUSB5100(self.idn)
                print('device closed successfully')
                self.initialized_gaussmeter = False
            except Exception as e:
                print('device did not close successfully. here is the error message:')
                print(e)
                self.initialized_gaussmeter = False
                
        else:
            print('probe is not initialized; aborting close_connection command')
            
        
if __name__ == '__main__':
    
    # initialize variables, nothing more.
    dev = FW_BELL_5180_gaussmeter() 
    
    # initialize connection with FW Bell.
    dev.initialize_gaussmeter( mode='dc-tesla' , rangeB=2 )
    
    print('Waiting for client connection.')
    
    # assuming that the gaussmeter was initialized fine, start the server socket
    if dev.initialized_gaussmeter is True:
        
        # initialize socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(1)
            conn, addr = s.accept()
            print(f"Connected by socket: {addr}")
            
        # start infinite loop (which can be killed by the client) to always listen 
        while True:  
            
            # try to get some data, then convert the byte string to a normal string
            cmd = conn.recv(1024)
            cmd = cmd.decode()
            
            # if the client socket is closing, re-initialize socket 
            if cmd == 'closing':
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((HOST, PORT))
                    s.listen(1)
                    conn, addr = s.accept()
                    print(f"Connected by socket: {addr}")
                cmd = ''
            
            # if there is nothing there, then don't continue with the rest of the loop, just try again.
            if not cmd:
                continue
            
            # output the received command
            print(f"\nReceived {cmd}")   
            
            if cmd == "Client to server: attempting to connect":
                res = "Server to client: connected."
            elif cmd == "Client to server: killServer":
                print('server terminated.')
                break
            elif cmd == 'isGaussmeterInitialized?':
                if dev.initialized_gaussmeter:
                    res = "yes"
                else:
                    res = "no"
            else:
                # actually execute the command here
                res = dev.direct_command(cmd)
                if not res:
                    res = "0"
                
            # print the sent results, and finally send the results
            # remember that "res" should be a normal string, which needs to be formatted to a bytestring.
            print(f"Sent {res}")
            conn.sendall(bytes(res,'utf-8'))
            
            
    
    
    # close the gaussmeter connection
    # maybe never reach this, luckily this doesn't seem to matter much, if at all.
    dev.close_connection()