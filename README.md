# fw_bell_5180_gaussmeter
Example Python Code for FW Bell 5180 Gaussmeter or Teslameter

This file is essentially a Python wrapper, based on ctypes, around the DLLs that FW Bell/Meggitt provide to interface with their 5180 Gauss/Teslameter.

This code is not intended as a drop-in module, but it is pretty close. It will at least let you a) connect to your probe and b) start collecting data with it. The ways that data is passed around is what you would have to modify. I'm not interested in wrapping every single little function; however, you can pass any arbitrary command with the "direct_command" class function, so that should get you pretty far in your goals.

Note that in or around line 78 there is a conditiona statement with "DEVICE ID 16a2:5100" in it. This is (I think) a unique identifier for my gaussmeter. This means that you need to put in your gaussmeter's ID. This is easy to do. Just uncomment the "print(dev_list)" on line 77. It will output the identifier of your device when you run the code. Once you have it, change line 78 to reflect this different ID and then comment line 77 again. Or just get rid of this entire section, it isn't really necessary. I just found that the probe isn't truly read to use for ~10 seconds after plugging into my computer, so that is what this code is for, monitoring for computer-gaussmeter connection before proceeding.

There are some interesting quirks, like I wasn't able to figure out how to set autoranging through this interface.

Calibration routine depends on a timer, as I could not figure out how to query the device to see if it was done calibrating. 

The reaons for all the "b"s in front of the strings is because ctypes expects byte strings, not normal strings, to pass to the DLL functions. This is also the purpose of the hidden _str_to_b_str()_, to do the conversion from normal string to byte string if needed.

Occasionally something goes wrong with the gaussmeter and you will get an error like "Windows has stopped this device because it has reported problems. (code 43)". I have tried holding down the "reset" button on the gaussmeter, turning the gaussmeter (or your computer) off and on, and re-installing software on the computer, and none of it seems to help. Weirdly, the only thing that seems to help is to plug the gaussmeter into another computer. The other computer doesn't even need to have the FW Bell software installed. It probably helps to uninstall the unidentified device in Windows Device Manager before plugging it back into your work computer.

HUGE CAVEAT: I have only been able to get this code to work with the 32-bit DLLs. There seems to be an issue loading the 64-bit libusb0.dll that they provided (as investigated from procmon). In theory, this code should work either either 32 or 64 bit DLLs. Of course, to run 32 bit dlls you have to be running 32 bit python, and to run 64 bit dlls you have to use 64 bit python, but this code itself should not need to change. 

You can see in the code where I tried to define where the 32 and 64 bit DLLs are located. Again, for some reason initialization fails with 64 bit codes, but works just fine with 32 bit codes. These are the DLLs that can be downloaded directly from their website, currently located here: https://fwbell.com/resources/software-downloads/ . Note that the 64 bit libraries need to be renamed. The "-x64" part needs to be removed, so that the names are just "usb5100.dll" and "libusb0.dll".


