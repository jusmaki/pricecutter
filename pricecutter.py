#!/usr/bin/env python3
import datetime
import socket
import sys
import time

import porssari
import pricecutter_httpserver
from config import device_mac, client

import automationhat
import st7735


json_version = "2"
#server = "http://localhost:8000/getcontrols.php?"
server = "https://api.porssari.fi/getcontrols.php?"
spot = "https://api.spot-hinta.fi/TodayAndDayForward"

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("""This example requires PIL.
Install with: sudo apt install python{v}-pil
""".format(v="" if sys.version_info.major == 2 else sys.version_info.major))
    sys.exit(1)


try:
    from fonts.ttf import RobotoBlack as UserFont
except ImportError:
    print("""This example requires the Roboto font.
Install with: sudo pip{v} install fonts font-roboto
""".format(v="" if sys.version_info.major == 2 else sys.version_info.major))
    sys.exit(1)

print("""pricecutter.py

This Automation HAT Mini application uses electricity price service to
cut off most expensive hours from relay.

Press CTRL+C to exit.
""")

def getip():
    testIP = "8.8.8.8"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((testIP, 0))
    ipaddr = s.getsockname()[0]
    s.close()
    return ipaddr

ipaddr = getip()

# Create ST7735 LCD display class.
disp = st7735.ST7735(
    port=0,
    cs=st7735.BG_SPI_CS_FRONT,
    dc=9,
    backlight=25,
    rotation=270,
    spi_speed_hz=4000000
)

# Initialise display.
disp.begin()

colour = (255, 181, 86)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
white = (255,255,255)
grey = (80,80,80)

font = ImageFont.truetype(UserFont, 12)
numbers = ImageFont.truetype(UserFont, 11)

# Values to keep everything aligned nicely.
text_x = 110
text_y = 34

bar_x = 25
bar_y = 37
bar_height = 8
bar_width = 73


relays = {}

def relay_function(id, state):
    print("Set relay to ", id, state)
    relays[id] = state
    if state == "1":
        automationhat.relay.one.on()
    elif state == "0":
        automationhat.relay.one.off()
    

p = porssari.Porssari(device_mac=device_mac, client=client, relay_cb=relay_function)
p.start()

httpd = pricecutter_httpserver.start_pricecutter_httpserver(p)

while True:
    # Value to increment for spacing text and bars vertically.
    offset = 0
    # Open our background image.
    image = Image.open("images/blank.jpg")
    draw = ImageDraw.Draw(image)

    # Draw the IP-address
    draw.text((20,0), "http://" + ipaddr+ ":3000", font=font, fill=colour)
    # Draw current time
    now = datetime.datetime.now()
    draw.text((20,12), now.isoformat()[0:19], font=font, fill=colour)
    # Draw current price
    draw.text((20,24), f"Duration: {p.get_time_to_relay_update()}", font=font, fill=colour)
    # Draw info on relay current state
    state = relays.get('1', "Power TBD")
    state_colour = grey
    if state == '0':
        state = "Power OFF"
        state_colour = red
    elif state == '1':
        state = "Power ON"
        state_colour = green
    draw.text((20,36), state, font=font, fill=state_colour)
    # Draw time to indicate updates to relay control
    hours = p.get_on_off_hours()
    if len(hours) > 0:
        sorted_hours = sorted(hours.keys())
        start_time = sorted_hours[0]
        start_hour = datetime.datetime.fromtimestamp(start_time).hour
        start_minute = datetime.datetime.fromtimestamp(start_time).minute
        last_printed_hour = ""
        for t in hours:
            t0 = t - start_time
            hour = t0 / 3600
            state = hours[t]
            thour = datetime.datetime.fromtimestamp(t).hour
            c = grey
            if state == '0':
                c = red
            elif state == '1':
                c = green
            draw.rectangle((20 + hour*5, 50, 20 + hour*5 + 4, 50 + 10), c)
            if (thour % 6) == 0 and last_printed_hour != thour:
                draw.text((20 + hour*5, 60), str(thour), font=numbers, fill=white)
                last_printed_hour = thour
        xhour = (now.hour - start_hour)* 5 + (now.minute-start_minute)*5/60
        draw.line(((20 + xhour, 80), (20+ xhour, 67)), width=4,fill=blue)

    # Draw the image to the display.
    disp.display(image)
    time.sleep(10.0)
