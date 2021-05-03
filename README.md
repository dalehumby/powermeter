# Power Meter for recording electricity usage at home using MicroPython on ESP8266.

![Installed hardware](/images/installed.jpg)

Assumes your power meter has a flashing LED that flashes every e.g 1/1000th of
a kWh and that you can place an optotransistor over the LED to trigger a pulse
on a pin on the ESP8266.

Features
- Web page at `/` to get and set the kWh remaining on your prepaid electricity meter
- Prometheus `/metrics` endpoint to get details about power usage for display in Grafana
- Link to Home Assistant and Node-Red by publishing on the MQTT `powermeter` topic

Tested with 
- MicroPython 1.13
- Wemos D1 Mini ESP8266

![Web server](/images/web.png)
![Prometheus metrics](/images/prometheus.png)

# How to set up

## Install USB to serial drivers on MacOS
https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all

## How to install MicroPython on ESP8266 board
From https://docs.micropython.org/en/latest/esp8266/tutorial/intro.html
Downloaded latest MicroPython 1.13: esp8266-20200911-v1.13.bin
pip3 install esptool

`esptool.py --help`

`esptool.py erase_flash`

`esptool.py --port /dev/tty.wchusbserial1410 --baud 460800 write_flash --flash_size=detect 0 ~/Downloads/esp8266-20200911-v1.13.bin`

## Connect to the boards REPL using WebREPL
http://micropython.org/webrepl/#10.0.0.146:8266

## Using Ampy to connect to dev board
Command line tool for upload/download of files. 
Installation instructions at https://github.com/scientifichackers/ampy

- List files `ampy -p /dev/tty.wchusbserial1410 -b 115200 ls`
- Run a file (even if it's not yet uploaded) `ampy -p /dev/tty.wchusbserial1410 -b 115200 run main.py`
- Upload a file `ampy -p /dev/tty.wchusbserial1410 -b 115200 put main.py`
- Upload all the files: `boot.py`, `main.py`, `config.json`, `index.html`, `metrics`
- Note you will need to edit `config_example.json` to suit your requirements, and save as `config.json`

## Use Screen to view terminal output

- `screen /dev/tty.wchusbserial1410 115200`
- To exit from Screen: `CTRL+A` `CTRL+\`
- To abort the currently running program, get back to REPL: `CTRL+C`
- To restart micro: `CTRL+D`

# Where to buy
- [Communica](https://www.communica.co.za/products/bmt-d1-mini-pro-esp8266-16m-ant) or [Micro Robotics](https://www.robotics.org.za/MINI-D1-4M) supply a cheap [D1 Mini board](https://www.wemos.cc/en/latest/tutorials/d1/get_started_with_micropython_d1.html)
- [Ambient light sensor](https://www.communica.co.za/products/bmt-ambient-light-sensor), also from Communica, but pretty much any light dependent resistor (LDR) or optotransistor board will work

# Learn More
 I made a full presentation on [Home Automation with MicroPython, the ESP8266 and Google Home](http://www.dalehumby.com/blog/Home-automation-with-MicroPython/) at Google DevFest 2020. It includes my slides and [YouTube presentation](https://youtu.be/pRu_9WTazDM?t=969) for building this Power Meter, as well as a short intro to MicroPython.
 
