#from setuptools import Extension, setup
from Cython.Build import cythonize
#setup( ext_modules = cythonize([Extension("fwb", ["FWB5180_pythonWrapper.pyx"])]) )

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
    Extension('fwb',
              ['FWB5180_pythonWrapper.pyx'],
              language="c++",  
              libraries=['usb5100','libusb0'],
              library_dirs=['C:\\Users\\Ben\\Documents\\UCLA\\Research\\Hardware\\fw_bell_magnetic_field_probe\\usb5100-x64\\x64-dist\\cython_attempt_2\\'])
    ]

setup(
    name = 'FWB python wrapper',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)




