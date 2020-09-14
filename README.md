# Power Meter for recording electricity usage at home using MicroPython on ESP8266.

Assumes your power meter has a flashing LED that flashes every e.g 1/1000th of
a kWh and that you can place an optotransistor over the LED to trigger a pulse
on a pin on the ESP8266.

Presents a
- Web page at `/` to get and set the kWh remaining on your prepaid electricity meter
- Prometheus `/metrics` endpoint to get details about power usage
- (FUTURE) Link to Home Assistant

Tested with MicroPython 1.13

# How to set up

## Install USB to serial drivers on MacOS
https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all

## How to install MicroPython on ESP8266 board
TODO

## Connect to the boards REPL using WebREPL
http://micropython.org/webrepl/#10.0.0.146:8266

## Using Ampy to connect to dev board
Command line tool for upload/download of files. 
Installation instructions at https://github.com/scientifichackers/ampy

- List files `ampy -p /dev/tty.wchusbserial1410 -b 115200 ls`
- Run a file (even if it's not yet uploaded) `ampy -p /dev/tty.wchusbserial1410 -b 115200 run main.py`
- Upload a file `ampy -p /dev/tty.wchusbserial1410 -b 115200 put main.py`

## Use Screen to view terminal output

- `screen /dev/tty.wchusbserial1410 115200`
- To exit from Screen: `CTRL+A` `CTRL+\`
- To abort the currently running program, get back to REPL: `CTRL+C`
- To restart micro: `CTRL+D`
 
