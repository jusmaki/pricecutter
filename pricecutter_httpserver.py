#!/usr/bin/python3
"""
The PriceCutterHttpServer module runs a small HTTP locally
for getting the status of the control module with HTTP.
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import time
import datetime
import base64
from threading import Thread, current_thread

html="""
<html>
<head>
  <meta http-equiv="refresh" content="600">
  <title>Price Cutter</title>
  <style>
    body {
      background-color: black;
      color: #ffB556;
    }
  </style>
</head>
<body>
PriceCutter $DATE<br>
Update config at <a href="https://porssari.fi">porssari.fi</a><br>
Price-information at <a href="http://www.sahko.tk">www.sahko.tk</a><br>
Price: $PRICE<br>
Duration: $UPDATE<br>
$POWER<br>
<div class="btn-group">
  $MODES
</div>
</body>
</html>
"""

FAVICON_BASE64="""
AAABAAEAEBAAAAEAIAAoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/
AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A
AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA
AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA
/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A/wD/AP8A/wD/AP8A/wD/
AP8A/wAAAP8AAAD/AAD//wAA//8AAP//AAD//wAA//8AAAD/AAAA/wAAAP8AAAD/AP8A/wD/AP8A
/wD/AP8A/wD/AP8AAAD/AAAA/wAA//8AAP//AAD//wAA//8AAP//AAAA/wAAAP8AAAD/AAAA/wD/
AP8A/wD/AP8A/wD/AP8A/wD/AAAA/wAAAP8AAP//AAD//wAA//8AAP//AAD//wAAAP8AAAD/AAAA
/wAAAP8A/wD/AP8A/wD/AP8A/wD/AP8A/wAAAP8AAAD/AAD//wAA//8AAP//AAD//wAA//8AAAD/
AAAA/wAAAP8AAAD/AP8A/wD/AP8A/wD/AP8A/wD/AP8AAAD/AAAA/wAA//8AAP//AAD//wAA//8A
AP//AAAA/wAAAP8AAAD/AAAA/wD/AP8A/wD/AP8A/wD/AP8A/wD/AAAA/wAAAP8AAP//AAD//wAA
//8AAP//AAD//wAAAP8AAAD/AAAA/wAAAP8A/wD/AP8A/wD/AP8A/wD/AP8A/wAAAP8AAAD/AAD/
/wAA//8AAP//AAD//wAA//8AAAD/AAAA/wAAAP8AAAD/AP8A/wD/AP8A/wD/AP8A/wD/AP8AAAD/
AAAA/wAA//8AAP//AAD//wAA//8AAP//AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A
AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA
AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA
/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/
AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A
AAD/"""

class PriceCutterHttpHandler(BaseHTTPRequestHandler):
    timeout = 1

    def __init__(self, porssari):
        self.porssari = porssari

    def __call__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        print("DEBUG: Request arrived")
        if "/favicon.ico" in self.path:
        # Send the favicon response
            self.send_response(200)
            self.send_header('Content-Type', 'image/x-icon')
            self.end_headers()

            # Write the binary data for the favicon
            favicon_data = base64.b64decode(FAVICON_BASE64)
            self.wfile.write(favicon_data)
            return
        if "/script.js" in self.path:
            with open("script.js", "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript")
                self.end_headers()
                self.wfile.write(f.read())
                return
        print("DEBUG Processing request")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        DATE = datetime.datetime.now().replace(microsecond=0).isoformat()
        state = self.porssari.get_state("1")
        POWER="Power: OFF"
        if state == "1":
            POWER="Power: ON"
        UPDATE=self.porssari.get_time_to_relay_update()
        MODES = ""
        PRICE = ""
        hours = self.porssari.get_on_off_hours(accuracy=3600)
        spot_array = self.porssari.get_spot_price()
        price = "0.0"
        if len(hours) > 0:
            sorted_hours = sorted(hours.keys())
            start_time = sorted_hours[0]
            start_datetime = datetime.datetime.fromtimestamp(start_time)
            start_hour = start_datetime.hour
            start_minute = start_datetime.minute
            last_printed_hour = ""
            for t in hours:
                t0 = t - start_time
                hour = t0 / 3600
                state = hours[t]
                t_datetime = datetime.datetime.fromtimestamp(t)
                thour = t_datetime.hour

                lookup_time = f"{t_datetime.year}-{t_datetime.month:02d}-{t_datetime.day:02d}T{thour:02d}"
                for spot in spot_array:
                    if lookup_time in spot.get('DateTime'):
                        priceNoTax = spot.get('PriceNoTax', 0)*1000 ## convert EUR/kWh to EUR/MWh
                        price = f"{priceNoTax:.1f}"
                        if PRICE == "":
                            PRICE = f"{priceNoTax:.1f} &#8364;/MWh {priceNoTax/10:.2f} c/kWh"
                        
                if state == '0':
                    c = "red"
                else:
                    c = "lime"
                MODES = MODES + f'<button class="default" title="H00" style="color:black;padding:1px 1px;background-color:{c};width:40px;border:1px solid white;height:40px;font-size:12px">{thour}<br>{price}</button>'
            
        body = html.replace("$DATE", DATE) \
             .replace("$POWER", POWER) \
             .replace("$UPDATE", UPDATE) \
             .replace("$PRICE", PRICE) \
             .replace("$MODES", MODES)

        self.wfile.write(body.encode())
        print("DEBUG RESPONSE sent")


def start_pricecutter_httpserver(porssari):
    """Start http server.

    Parameters
    ----------
    porssari: porssari object providing methods to fetch current state, 
    time to update and next hours relay states.
    """
    def serve_forever(httpd):
        httpd.timeout = 1
        with httpd:
            httpd.serve_forever()

    port = 3000
    handler = PriceCutterHttpHandler(porssari)
    httpd = ThreadingHTTPServer(('', port), handler)
    httpd.timeout = 1
    httpd.allow_reuse_address = True
    #httpd.server_bind() ## Already called in HTTPServer
    httpd.server_activate()
    thread = Thread(target=serve_forever, args=(httpd,))
    thread.setDaemon(True)
    thread.start()
    return httpd

#######################################################################
# Test code

class MockPorssari:
    def __init__(self,
                 server="https://api.porssari.fi/getcontrols.php?",
                 device_mac=None,
                 client=None,
                 relay_cb=None, # usage relay_cb(relay_id, state)
                 update_interval = 15*60): # fetch data by default in 15 minute
        self.relay_cb = relay_cb
        self.relays = {}
        pass

    def start(self):
        self.relays["1"] = "1"
        relay_cb("1","1")

    def get_on_off_hours(self):
        return []

    def get_time_to_relay_update(self):
        return "10m"

    def get_state(self, id):
        return self.relays.get(id)

mockrelays = {}
    
def mockrelay(id, state):
    mockrelays[id] = state
    
def test():
    p = MockPorssari(relay_cb=mockrelay)
    start_pricecutter_httpserver(p)
    time.sleep(3600)

if __name__ == "__main__":
    test()
