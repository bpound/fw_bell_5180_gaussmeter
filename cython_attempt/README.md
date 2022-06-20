This was my attempt at Cython wrapping the DLL. But Cython doesn't work too great with DLLs, it seems you have to have a .lib file. But the .lib files were not provided. Turns out that you can convert a DLL to a LIB file. That is the reason for the implib.bat file. Run it at the command line, and pass the dll name. So like "implib.bat usb5100.dll", and it will output a lib file in this same folder. Note the "/machine:x64" on the last line is for 64 bit LIB files. If you need 32 bit, you would change it to "/machine:x86".

Otherwise this is a standard cython project, where c_FWB5180.pxd is the Cython interface with the header file, FWB5180_pythonWrapper.pyx is the actual python wrapper, and setup.py is the compilation and linking script. It is run with "python setup.py built_ext --inplace", and in this case a file called "fwb.cp39-win_amd64.pyd", which can be imported (as shown in attempt_at_import.py) as "import fwb". But I still got access violation errors with this file, so I gave up. But at least it compiled.