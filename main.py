import gc

import btree
import esp
import network
import ujson
import usocket as socket
from machine import Pin


def handle_input_pin(state):
    """Interrupt handler routine for input pin state change."""
    global kwh
    kwh = kwh - kwh_per_flash
    # TODO every change by 0.1 kWh write to DB
    # TODO change the kwh thing to a class with DB stuff hidden within


def handle_get():
    """
    Handle the http GET method

    Retrieve the latest stats and return the rendered webpage
    """
    return index_template.format(kwh=kwh)


def handle_post(request):
    """Handle the http POST method.

    Get the request, pull out the kwh and persist
    """
    global kwh
    loc = request.find("kwh=")
    param = request[loc:-1]
    kwh = float(param.split("=")[1])
    db[b"kwh"] = str(kwh)
    db.flush()
    print("Saved new kWh to DB: {kwh}".format(kwh=kwh))


esp.osdebug(None)

with open("config.json", "r") as f:
    config = ujson.load(f)

with open("index.html", "r") as f:
    index_template = f.read()

# Open or create the database
try:
    dbfile = open("db", "r+b")
    print("Opened DB")
except OSError:
    dbfile = open("db", "w+b")
    print("Created DB")
db = btree.open(dbfile)

# Initialise the kwh value if it's not in DB
if b"kwh" not in db:
    db["kwh"] = str(0)
    db.flush()
    print("Initialised DB")
kwh = float(db[b"kwh"])
kwh_per_flash = 1 / config["pulse_per_kwh"]

# Setup hardware
input_pin = Pin(config["input_pin"], Pin.IN, Pin.PULL_UP)
input_pin.irq(trigger=Pin.IRQ_RISING, handler=handle_input_pin)

# Setup Wifi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(config["wifi"]["ssid"], config["wifi"]["password"])
while not station.isconnected():
    pass
print("Connected to wifi")
print(station.ifconfig())
gc.collect()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 80))
s.listen(5)
print("Ready for connections")

while True:
    conn, addr = s.accept()
    print("Got a connection from %s" % str(addr))
    request = str(conn.recv(1024))
    print("Content = %s" % request)
    if request.find("GET / ") >= 0:
        print("Handle GET")
        response = handle_get()
        conn.send("HTTP/1.1 200 OK\n")
        conn.send("Content-Type: text/html\n")
    elif request.find("POST / ") >= 0:
        print("Handle POST")
        if request.find("kwh=") < 0:
            # Browsers send a lot of headers, so try get more data if not found body yet
            request = str(conn.recv(1024))
        handle_post(request)
        # Redirect back to /
        conn.send("HTTP/1.1 301 Found\n")
        conn.send("Location: /\n")
        response = None
    else:
        print("Not found")
        conn.send("HTTP/1.1 404 Not Found\n")
        response = None
    conn.send("Connection: close\n\n")
    if response:
        conn.sendall(response)
    conn.close()
    gc.collect()

# This will never be executed
db.close()
dbfile.close()
