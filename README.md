# Experiments with MicroPython on ESPDUINO

## Install USB to serial drivers on MacOS
https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all

## WebREPL
http://micropython.org/webrepl/#10.0.0.146:8266

## Using Ampy to connect to dev board
Command line tool for upload/download of files. 
Installation instructions at https://github.com/scientifichackers/ampy

- List files `ampy -p /dev/tty.wchusbserial1410 -b 115200 ls`
- Run a file (even if it's not yet uploaded) `ampy -p /dev/tty.wchusbserial1410 -b 115200 run main.py`
 
