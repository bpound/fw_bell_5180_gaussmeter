# fw_bell_5180_gaussmeter
Example Python Code for FW Bell 5180 Gaussmeter or Teslameter


This file is essentially a Python wrapper, based on ctypes, around the DLLs that FW Bell/Meggitt provide to interface with their 5180 Gauss/Teslameter.

This code is not intended as a drop-in module, but it is pretty close. It will at least let you a) connect to your probe and b) start collecting data with it. The ways that data is passed around is what you would have to modify. I'm not interested in wrapping every single little function; however, you can pass any arbitrary command with the "direct_command" class function, so that should get you pretty far in your goals.

You can see in the code where I tried to define where the 32 and 64 bit DLLs are located. Again, for some reason initialization fails with 64 bit codes, but works just fine with 32 bit codes.

The reaons for all the "b"s in front of the strings is because ctypes expects byte strings, not normal strings, to pass to the DLL functions. This is also the purpose of the hidden _str_to_b_str()_, to do the conversion from normal string to byte string if needed.

Huge caveat: I have only been able to get this code to work with the 32-bit DLLs. There seems to be an issue loading the 64-bit libusb0.dll that they provided (as investigated from procmon). In theory, this code should work either either 32 or 64 bit DLLs. Of course, to run 32 bit dlls you have to be running 32 bit python, and to run 64 bit dlls you have to use 64 bit python, but this code itself should not need to change. 

There are some interesting quirks, like I wasn't able to figure out how to set autoranging through this interface, but for the most part it seems to work fine. 

Calibration routine depends on a timer, as I could not figure out how to query the device to see if it was done calibrating. 
