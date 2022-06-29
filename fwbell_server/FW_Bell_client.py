# echo-client.py

import socket,time


class FW_Bell_gaussmeter_client():
    def __init__(self,mode='d',rangeB='b',HOST="127.0.0.1",PORT=65432,printRes=False):
        """
        HOST = 127.0.0.1 - this is the IP address over which to communicate. As this is a completely local (i.e. same computer) interaction, use 127.0.0.1 since it is the loopback IP address
        PORT = 65432 - this is the port over which communication happens. This is a randomly chosen value, it can be anything between 1024 and 65532 as those are unprivileged ports. So if there is weird behavior, change the port (NOT THE HOST!! probably.)
        """
        
        self.HOST = HOST  #the server's hostname or IP address (since this is on the same computer, use loopback of 127.0.0.1)
        self.PORT = PORT  #the port used by the server (use some random number above 1023
        
        self.PR = printRes
        
        # initialize socket
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((HOST, PORT))
            self.initialized = True
        except:
            self.initialized = False
           
        # see if the gauss probe is initialized
        self.initialized_probe = False
        if self.initialized:
            print('here')
            try:
                print('here 2')
                cmd = 'isGaussmeterInitialized?'
                print('here 3')
                res = self.send_msg(cmd,verbose = True)
                print('here 4')
                print(res)
                
                if str(res,'utf-8') == "yes":
                    self.initialized_probe = True
                else:
                    self.initialized_probe = False
            except Exception as e:
                print(e)
                self.initialized_probe = False
                  
        else:
            self.initialized_probe = False
                
            
        
    def calibrate(self,doAutomatically = False):
    
        if doAutomatically is False:
            input('press enter when ready to start calibration')
            
        # do the calibration
        cmd = ":SYSTEM:AZERO"
        print('starting calibration')
        
        status = self.send_msg(cmd,verbose=True)

        # takes about 5 seconds to calibrate, add a second for security buffer
        time.sleep(6)
        print('status of calibration: ',status)
        
        
    def send_msg(self,cmd,verbose = False):
    
        if self.initialized:
            self.s.sendall( bytes(cmd,'utf-8') )
            
            if verbose or self.PR: print(f"\nSent {cmd}")
            
            response = self.s.recv(1024)
            response = str( response , 'utf-8')
            
            if verbose or self.PR: print(f"Received {response}")
        else:
            if verbose or self.PR: print(f"not initialized, cannot do command")
            response = -100000000
            
        return response
        
    def test_network_connection(self):
        msg = "Client to server: attempting to connect"
        response = self.send_msg( msg , verbose = True )
        if response == "Server to client: connected.":
            self.server_connection = True
    
    def read_magnetic_field(self):
    
        response = self.send_msg(":MEASURE:FLUX?",verbose = False) 
        #print('intermediate response: ',response)
        
        if response[:5] == 'error':
            print('it appears there was an error. See the output: ',response)
            val = [-1,'error']
            
        else:
            # resp.value gives a string like '-0.162T', so you need to strip off the first b' and the last T'. Hence the slicing.
            if 'mT' in response:
                flux_value = float(response[:-2])
                val = [flux_value,'mT']
            elif 'T' in response:
                flux_value = float(response[:-1])
                val = [flux_value,'T']
            elif 'G' in response:
                flux_value = float(response[:-1])
                val = [flux_value,'G']
            #print('further processed string (right before num conversion): ', val)
        
        if self.PR:
            print(f"measured flux value: {val[0]} {val[1]}")
            
        return val
             
    def apply_settings(self,rangeB= 'd', mode='d'):
    
    
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
        
        
        newcmd = bytes(cmd , 'utf-8')
        self.s.sendall(newcmd)
        status = str(self.s.recv(1024),'utf-8')
        print('status of mode setting: ', cmd , ' : ',status)

        
        
        # do measurement range:
        cmd_str = ':SENSE:FLUX:RANGE'
        if rangeB == 0: cmd = cmd_str+' 0' # the space in these is intentional
        elif rangeB == 1: cmd = cmd_str+' 1'
        elif rangeB == 2: cmd = cmd_str+' 2'
        elif rangeB == -1: cmd = cmd_str+':AUTO'
        else: cmd = cmd_str+':AUTO' # do autorange by default

        newcmd = bytes(cmd , 'utf-8')
        self.s.sendall(newcmd)
        status = str(self.s.recv(1024),'utf-8')
        print('range setting command : status of mode setting: ', cmd , ' : ',status)
        
        # get weird readings without a pause of at least 1 second. 
        # not too worried since we don't need to change settings that often.
        time.sleep(1.5)
        
    def kill_server(self):
        self.s.sendall(b"Client to server: killServer")
    def close(self):

        # client socket is closing, tell server it needs to re-update the socket connection
        self.s.sendall(bytes('closing', 'utf-8'))
        try:
            self.s.close()
        except:
            pass
            
    def all_close(self):
        try:
            self.kill_server()
        except:
            print('server already terminated.')
        print('closed gaussmeter and connection')
        
        self.close()
        print('closed local socket connection')

if __name__ == '__main__':

    dev = FW_Bell_gaussmeter_client(printRes = False)
    dev.test_network_connection()
    dev.apply_settings( mode = 'dc-tesla' , rangeB=0 )
    
    #dev.calibrate()
    
    
    res = dev.read_magnetic_field()
    
    
    dev.close()