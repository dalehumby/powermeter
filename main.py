"""
Power Meter for recording electricity usage at home using MicroPython on ESP8266.

Tested with
- MicroPython 1.13
- Wemos D1 Mini:
  - https://www.wemos.cc/en/latest/d1/d1_mini.html
  - Pinout https://randomnerdtutorials.com/esp8266-pinout-reference-gpios/
"""

import gc

import btree
import esp
import network
import ntptime
import ujson as json
import usocket as socket
import utime as time
from machine import RTC, Pin, Timer
from micropython import alloc_emergency_exception_buf, schedule

MS_IN_MINUTE = 1000 * 60
MS_IN_HOUR = MS_IN_MINUTE * 60
UNIX_EPOCH_OFFSET = 946684800  # Seconds between Unix Epoch (1 Jan 1970) and MicroPython Epoch (1 Jan 2000)


def mean(lst):
    """Helper function to calculate the mean of the values in a list."""
    return sum(lst) / len(lst)


class PowerMeter:
    """
    Keep track of the kWh used.

    kwh: Number of kWh remaining on the power meter. Should match the power meters LCD.
    """

    def __init__(self, pulse_per_kwh):
        """Setup, including initialsing the database if it doesnt exist."""
        self._kwh_per_pulse = 1 / pulse_per_kwh
        self._round = (
            len(str(pulse_per_kwh)) - 1
        )  # Hacky way to get order of magnitude. No log10
        self._persist_counter = 0
        self._debounce_time = time.ticks_ms()

        # Setup DB
        try:
            self._dbfile = open("db", "r+b")
            print("Opened DB")
        except OSError:
            self._dbfile = open("db", "w+b")
            print("Created DB")
        self._db = btree.open(self._dbfile)
        if b"kwh" not in self._db:
            self._db["kwh"] = str(0)
            self._db.flush()
            print("Initialised DB")
        self._kwh = float(self._db[b"kwh"])

        # Setup averages
        self.timestamp = "NaN"
        self._timer = Timer(-1)
        self._timer.init(
            period=MS_IN_MINUTE, mode=Timer.PERIODIC, callback=self.timer_handler
        )
        self._pulses_per_minute = 0
        self.kw_history = []
        self.joules = 0

    @property
    def kwh(self):
        return self._kwh

    @kwh.setter
    def kwh(self, value):
        """Set a new kWh and persist to DB."""
        self._kwh = value
        self._db[b"kwh"] = str(self._kwh)
        self._db.flush()
        print("Saved kWh to DB: {kwh}".format(kwh=self._kwh))

    def count(self, amount):
        """
        Keep track of power usage.

        Count the number of pulses since startup.
        Decrement the kWh by `amount` of pulses each time this is called.
        Only write to flash periodically.
        """
        if time.ticks_diff(time.ticks_ms(), self._debounce_time) < 50:
            print("Debounce")
            return
        print("Count")
        self._debounce_time = time.ticks_ms()
        self._pulses_per_minute += amount
        self._kwh = round(
            self._kwh - amount * self._kwh_per_pulse, self._round
        )  # Handle float issues by rounding
        self._persist_counter += 1
        if self._persist_counter % 100 == 0:
            self._persist_counter = 0
            self.kwh = self._kwh

    def timer_handler(self, timer_id):
        """
        Calculate the average power usage per minute.

        Keep history of last 120 minutes.
        """
        print("Pulses in last 1 min:", self._pulses_per_minute)
        avg_kw_1min = self._pulses_per_minute * 60 * self._kwh_per_pulse
        self._pulses_per_minute = 0
        self.kw_history.append(avg_kw_1min)
        self.kw_history = self.kw_history[-120:]
        self.joules += avg_kw_1min * 1000 * 60  # 1 J = 1 W.s
        self.timestamp = (time.time() + UNIX_EPOCH_OFFSET) * 1000
        print("1 min avg:", avg_kw_1min, "kW")
        print("Total Joules since startup", self.joules, "J")
        print("Last 120 min:", self.kw_history)


def pulse_isr(state):
    """
    Interrupt service routine for input pin state change.

    Schedule the decrement outside of the ISR.
    """
    print("Pulse ISR triggred", end=" ")
    schedule(power_meter.count, 1)
    # Idea: Sometimes get "RuntimeError: schedule queue full", so could put a try/except block
    # and keep a count of times couldnt schedule the dec call, and then hand the count to dec
    # May not be necessary because even at 50 A there are only 3.33 pulses per second


def resync_rtc(timer_id):
    """
    Resync the RTC to NTP every 1 hour.

    See http://docs.micropython.org/en/latest/esp8266/general.html?highlight=ntptime#real-time-clock"""
    ntptime.settime()
    print("Resync RTC to", rtc.datetime())


def handle_get():
    """
    Handle the http GET method.

    Retrieve the latest stats and return the rendered webpage.
    """
    return index_template.format(kwh=power_meter.kwh)


def handle_post(request):
    """
    Handle the http POST method.

    Get the request, pull out the kwh and persist.
    """
    loc = request.find(b"kwh=")
    param = request[loc:]
    power_meter.kwh = float(param.split(b"=")[1])


def handle_metrics():
    """
    Handle the Prometheus metrics request.

    Prometheus timestamps are ms since Unix Epoch 1 Jan 1970.
    Ref https://prometheus.io/docs/instrumenting/exposition_formats/
    """
    if power_meter.kw_history:
        return metrics_template.format(
            timenow=(time.time() + UNIX_EPOCH_OFFSET) * 1000,
            timestamp=power_meter.timestamp,
            kwh=power_meter.kwh,
            watts_avg_1m=power_meter.kw_history[-1] * 1000,
            watts_avg_5m=mean(power_meter.kw_history[-5:]) * 1000,
            watts_avg_15m=mean(power_meter.kw_history[-15:]) * 1000,
            watts_avg_60m=mean(power_meter.kw_history[-60:]) * 1000,
            watts_avg_120m=mean(power_meter.kw_history[-120:]) * 1000,
            joules=power_meter.joules,
        )
    else:
        return "# Please wait 1 min for metrics"


esp.osdebug(None)
alloc_emergency_exception_buf(100)
print("Waiting 2s before starting up... press CTRL+C to abort")
time.sleep(2)

with open("config.json", "r") as f:
    config = json.load(f)

with open("index.html", "r") as f:
    index_template = f.read()

with open("metrics", "r") as f:
    metrics_template = f.read()

power_meter = PowerMeter(config["pulse_per_kwh"])

# Setup hardware
pulse_pin = Pin(config["pulse_pin"], Pin.IN)
pulse_pin.irq(handler=pulse_isr, trigger=Pin.IRQ_RISING)
led_pin = Pin(
    config["led_pin"], Pin.IN, Pin.PULL_UP
)  # Set high impedence, turns off led

# Setup Wifi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(config["wifi"]["ssid"], config["wifi"]["password"])
while not station.isconnected():
    pass
print("Connected to wifi")
# Set up static IP address if a static IP has been configured
if "ip" in config["wifi"]:
    ifconfig = list(station.ifconfig())
    ifconfig[0] = config["wifi"]["ip"]
    station.ifconfig(tuple(ifconfig))
print(station.ifconfig())

# Setup realtime clock
rtc = RTC()
ntptime.settime()
print("Set time to", rtc.datetime())
resync_rtc_timer = Timer(-1)
resync_rtc_timer.init(period=MS_IN_HOUR, mode=Timer.PERIODIC, callback=resync_rtc)

# Run garbage collector
gc.collect()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 80))
s.listen(5)
print("Ready for http connections")

while True:
    conn, addr = s.accept()
    print("Got a connection from", str(addr))
    request = conn.recv(1024)
    print(request)
    if request.find(b"GET / ") >= 0:
        print("Handle GET")
        response = handle_get()
        conn.send("HTTP/1.1 200 OK\n")
        conn.send("Content-Type: text/html\n")
    elif request.find(b"POST / ") >= 0:
        print("Handle POST")
        if request.find(b"\r\n\r\n") < 0:
            # Browsers send a lot of headers, so try get more data if not found body yet
            request = conn.recv(1024)
        handle_post(request)
        # Redirect back to /
        conn.send("HTTP/1.1 301 Found\n")
        conn.send("Location: /\n")
        response = None
    elif request.find(b"GET /metrics ") >= 0:
        print("Handle metrics")
        response = handle_metrics()
        conn.send("HTTP/1.1 200 OK\n")
        conn.send("Content-Type: text/plain\n")
    else:
        print("Not Found")
        conn.send("HTTP/1.1 404 Not Found\n")
        response = None
    conn.send("Connection: close\n\n")
    if response:
        conn.sendall(response)
    conn.close()
    gc.collect()
