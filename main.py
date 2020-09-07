import gc

import esp
import network
import ujson
import usocket as socket
from machine import Pin

esp.osdebug(None)

with open("config.json", "r") as f:
    config = ujson.load(f)
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(config["wifi"]["ssid"], config["wifi"]["password"])
while not station.isconnected():
    pass
print("Connected to wifi")
print(station.ifconfig())
gc.collect()

led = Pin(2, Pin.OUT)  # TODO replace with correct pin and handler function

with open("index.html", "r") as f:
    index_template = f.read()


def handle_get():
    """
    Handle the http GET method

    Retrieve the latest stats and return the rendered webpage
    """
    kwh = 100.3
    return index_template.format(kwh=kwh)


def handle_post(request):
    """Handle the http POST method.

    Get the request, pull out the kwh and persist
    """
    loc = request.find("kwh=")
    param = request[loc:-1]
    _, kwh = param.split("=")
    return float(kwh)


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
        kwh = handle_post(request)
        print(kwh)
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
