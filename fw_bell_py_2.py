# before running you may need to install pyusb module: pip install pyusb

import ctypes,time
import os 
import usb.core 

###########
# some universal defaults go here.
###########

MODE = 'dc-tesla'
RANGEB = 1

# paths to the 32 and 64 bit DLL files are hardcoded here.
#Note that usb5100.dll and libusb0.dll must be in the same directory
# Recommended to put 32 bit in one folder and 64 bit in another folder
# because for the calling sequence, they must be named as such, but the 64 bit have -x64 appended. To make the libraries work, you need to strip that part.
pathDLL_32bit = "C:\\Users\\Ben\\Documents\\UCLA\\Research\\Hardware\\fw_bell_magnetic_field_probe\\usb5100-x64\\x64-dist\\32bit\\"
pathDLL_64bit = "C:\\Users\\Ben\\Documents\\UCLA\\Research\\Hardware\\fw_bell_magnetic_field_probe\\usb5100-x64\\x64-dist\\64bit\\"

class FW_BELL_5180_gaussmeter():
    def __init__(self,mode=MODE,rangeB= RANGEB,length=80):
        """
        Purpose: class to initialize and use the FW Bell 5180 gaussmeter
        Inputs:
        -- mode='dc-tesla',dc-gauss','dc-am','ac-tesla','ac-gauss','ac-am'
        -- rangeB= -1 for auto, 0 (0 - 300 G) low range, 1 (1-3 kG) mid range, or 2 (2-30 kG) high field range. Note that the auto function doesn't seem to work (gets a syntax error), so its probably better to set the range yourself.
        
        """
        
        # save as defaults, for now.
        self.mode = mode
        self.rangeB = rangeB
        self.length = length # this is for the pointers that return statuses. The manual said 80 should be big enough, though I don't think there is much in the way of making a bigger buffer if needed (though I don't think its needed)

        # determines whether being run by 32 or 64 bit python
        if ctypes.sizeof(ctypes.c_void_p) == 4:
            pathDLL = pathDLL_32bit
            checkUSB = False
        
        else:
            pathDLL = pathDLL_64bit
            checkUSB = True
            
            
        # add the path to the dll directory search
        os.add_dll_directory(pathDLL)

        
        # this makes sure that the dll is found. No need to do anything about the libusb0.dll, the usb5100.dll automatically calls and loads it.
        dllName = pathDLL + "usb5100.dll" 
        
        # open DLL
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
        
        if checkUSB:
                
            flag = True
            
            # use usb.core to try to find the gaussmeter.
            # this is useful because the gaussmeter tends to not be ready for use for several seconds after being plugged in and initialized by windows.
            while flag:
                dev_list = usb.core.show_devices()
                if "DEVICE ID 16a2:5100" not in dev_list:
                    print('trying to find device')
                    time.sleep(1)
                else:
                    flag = False
                    
            print('Found the device, moving on: ',dev_list)
            

        # open device and save handle to self.idn. should be a 4-bit number, not zero. 
        self.initialized=False
        self.initialize_connection()
        self.test_connection()
        self.apply_settings(mode,rangeB)
            
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
        
    def direct_command(self,cmd,output='returned'):
        """
        Purpose: execute a user-specfied SCPI command. This is called by other helper functions.
        Inputs:
        -- cmd: command string to execute. Can be normal or byte string, this is checked
        -- output: list of ["None","printed", and or "returned"] to do nothing with the output, print to the terminal, or return the value. Can put in a list, i.e. for ['printed','returned'] to do both. 
        Only nomincal slicing of [2:-1] type is done, you may need to do more slicing for your purposes (like stripping the T from the measurement command)
        """
    
        if self.initialized:

            # do a check to make sure that cmd is a byte string, not a string, and do the conversion if necessary
            cmd = self._str_to_b_str(cmd)
            #cmd = b"*OPC?;" + cmd
                            
            # now that we have a byte string, try to execute the command
            try:
                resp= ctypes.create_string_buffer(self.length-1) # it automatically gets terminated by a 0 byte, so we need to create a string buffer with one fewer to account for this.
                            
                ret = self.scpiCommand( self.idn , ctypes.create_string_buffer(cmd) ,resp,self.length )
                string_value = str(repr(resp.value))
                val = string_value[2:-1]

            except Exception as e:
                print('that command (%s) did not work. The error is: '%(str(repr(resp.value))))
                print(e)
                val = 'ERROR'
        else:
            val = 'error - not initialized'
            

                
        if 'printed' in output:
            print(cmd , ': ', val)
        if 'returned' in output:
            return val
                
    def calibrate(self,doAutomatically=False):
        """
            purpose: calibrate the probe, which happens after the use presses enter or if doAutomatically is True
            inputs: doAutomatically (defaults to False). If True, there is no prompt for calibration, it just happens when the command is run. 
            outputs: none
        """
        
        if self.initialized:
        
            if doAutomatically is False:
                input('press enter when ready to start calibration')
                
            # do the calibration
            cmd = b":SYSTEM:AZERO"
            print('starting calibration')
            status = self.direct_command(cmd,output='returned')

            
            time.sleep(6)
            print('status of calibration: ',status)
   
    def apply_settings(self,mode='d',rangeB='d'):
        """
        Purpose: apply the specified settings.
        Inputs:
        -- mode='dc-tesla','dc-gauss','dc-am','ac-tesla','ac-gauss','ac-am'
        -- rangeB= -1 for auto, 0 (0 - 300 G) low range, 1 (1-3 kG) mid range, or 2 (2-30 kG) high field range
        Outputs: none
        """
    
        if self.initialized:
        
            # if 'd' is passed, then use the default, which is already programmed.
            if mode == 'd': 
                mode = self.mode
            elif mode in ['dc-tesla','dc-gauss','dc-am','ac-tesla','ac-gauss','ac-am']: # if it is a valid mode, then save it as the new mode
                self.mode = mode
            else:
                print('mode value is not valid. Needs to be one of dc-tesla,dc-gauss,dc-am,ac-tesla,ac-gauss,ac-am')
                print('keeping the default: ',self.mode)
                mode = self.mode
                
            # do the same thing with the range
            if rangeB == 'd': 
                rangeB = self.rangeB
            elif rangeB<3 and rangeB>=-1 and int(rangeB)==rangeB:
                self.rangeB = rangeB
            else:
                print('rangeB value is not valid. Needs to be an integer: -1 (auto range), 0 (low range, 0-300 G), 1 (mid range, 1-3 kG), 2 (high range, 2-30 kG)')
                print('keeping the default: ',self.rangeB)
                rangeB = self.rangeB

            # do units
            unit_str = ':UNIT:FLUX:'    
            if mode == 'dc-tesla': cmd = unit_str+'DC:TESLA'
            elif mode == 'dc-gauss': cmd = unit_str+'DC:GAUSS'
            elif mode == 'dc-am': cmd = unit_str+'DC:AM'
            elif mode == 'ac-tesla':cmd = unit_str+'AC:TESLA'
            elif mode == 'ac-gauss': cmd = unit_str+'AC:GAUSS'
            elif mode == 'ac-am': cmd = unit_str+'AC:AM'
            else: cmd = unit_str+'DC:TESLA' # just assume we want tesla in DC, since that is usually what we want.
            
            
            newcmd = self._str_to_b_str(cmd)
            print('mode setting command: ',newcmd)
            status = self.direct_command(newcmd,output='returned')
            print('status of mode setting: ', status)

            
            
            # do measurement range:
            cmd_str = ':SENSE:FLUX:RANGE'
            if rangeB == 0: cmd = cmd_str+' 0' # the space in these is intentional
            elif rangeB == 1: cmd = cmd_str+' 1'
            elif rangeB == 2: cmd = cmd_str+' 2'
            elif rangeB == -1: cmd = cmd_str+':AUTO'
            else: cmd = cmd_str+':AUTO' # do autorange by default
            newcmd = self._str_to_b_str(cmd)
            
            status = self.direct_command(newcmd,output='returned')
            print('sense command, result: ',newcmd, ",",status)
                             
    def initialize_connection(self):
        """
        Purpose: establish connectionw with FW Bell probe
        Inputs/Outputs: None
        """
    
        try:
            idn = self.openUSB5100()
            
            if idn != 0:
                print('initialization successful, id number: ',idn)
                self.initialized = True
                self.idn = idn
                
            else:
                print('initialization failed')
                self.idn = 0
                
        except Exception as e:
            print('initialization failed with error:')
            print(e)
            self.idn = 0
            
    def test_connection(self):
        """
        Purpose: to test the connection with the gauss probe by sending '*IDN?' and seeing if it will respond appropriately.
        Inputs/Outputs: none
        """
            
        if self.initialized:
            try:
                print('attempting to query with the identity command...')
                cmd = b"*IDN?"
                ret_str = self.direct_command(cmd,output='returned')
                
                if ret_str[:5] == 'error':
                    print('it appears there was an error. See the output.')
                    
                print('probe identity (or command status): ',ret_str)
                
            except Exception as e:
                print('identity command failed. here is the error message:')
                print(e)
        else:
            print('probe is not initialized; aborting test connection command')
    
    def measure_flux(self,output='returned'):
        """
        Purpose: measure magnetic flux
        Inputs:
        -- output: ['returned','printed', and/or None] - defaults to returned. Could pass the list of ['returned','printed'] to do both.
        Outputs:
        -- val: if output has 'returned' in it, then val is returned. It is a two-element list, of [flux value,unit]. flux value is a float, unit is a string.
        """
        
        if self.initialized:
            # put together command
            cmd = b":MEASURE:FLUX?"
            ret_str = self.direct_command(cmd,output)
            
            if ret_str[:5] == 'error':
                print('it appears there was an error. See the output: ',ret_str)
                val = [-1,'error']
                
            else:
                # resp.value gives a string like '-0.162T', so you need to strip off the first b' and the last T'. Hence the slicing.
                if 'mT' in ret_str:
                    flux_value = float(ret_str[:-2])
                    val = [flux_value,'mT']
                elif 'T' in ret_str:
                    flux_value = float(ret_str[:-1])
                    val = [flux_value,'T']
                elif 'G' in ret_str:
                    flux_value = float(ret_str[:-1])
                    val = [flux_value,'G']
                print('further processed string (right before num conversion): ', val)
            
            if 'printed' in output:
                print('measured flux value: ',flux_value)
            if 'returned' in output:
                return val
                
        else:
            print('probe is not initialized; aborting measure_flux command')
        
    def close_connection(self):
        """
        purpose: close connection
        inputs/output: none
        """
    
        if self.initialized:
            try:
                self.closeUSB5100(self.idn)
                print('device closed successfully')
                self.initialized = False
            except Exception as e:
                print('device did not close successfully. here is the error message:')
                print(e)
                self.initialized = False
                
        else:
            print('probe is not initialized; aborting close_connection command')
            
        
if __name__ == '__main__':
    
    dev = FW_BELL_5180_gaussmeter() # this initializes the connection, sets the initial settings, and tests the connection
    
    
    dev.calibrate() # this will start the calibration routine (it will prompt the user to press enter when calibration is to start)
    
    
    # measure the flux five times
    fluxL = [] # flux list where I will store the values
    for ii in range(5):
        val = dev.measure_flux()
        fluxL.append(val[0]) # just pluck out the flux value, not the unit
        time.sleep(1)       # pause the loop for 1 second
        
    print('Here are the measured flux values:')
    print(fluxL)
    
    ## here is an example of how to use the direct_command method directly for purposes not explicitly detailed here.
    # we try to load any error that the gaussmeter might have, and show it.
    status = dev.direct_command(b':SYSTEM:ERROR?')
    print('error status: ',status)
    
    # here we clear all the system errors
    status = dev.direct_command(b':SYSTEM:CLEAR')
    print('clear error status: ',status)
    
    # close the connection to the gaussmeter
    dev.close_connection()
    
    
    



#scpiCommand = fwbell.scpiCommand

#scpiCommand.argtypes = [ctypes.c_ulong,ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char),ctypes.c_int]
#scpiCommand.argtypes = [ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int]
#scpiCommand.restype = ctypes.c_int


#length = ctypes.c_int(80)
#print(length,type(length))
#resp= ctypes.cast(ctypes.create_string_buffer(length.value-1),ctypes.POINTER(ctypes.c_char))
#ret = scpiCommand( ctypes.c_int(idn) , ctypes.create_string_buffer(b"*IDN?") , resp , length )
#":MEASURE:FLUX?"

#print(ret)

