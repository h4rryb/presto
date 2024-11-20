'''
A demo for the Pimoroni Presto.
Shows the current, next and last energy price for Octopus Energys Agile Price tarrif
'''

import network
import time
import requests
import ntptime
import datetime
from picographics import PicoGraphics, DISPLAY_PRESTO
from presto import Presto
from picovector import PicoVector, ANTIALIAS_BEST, Polygon, Transform

# Check and import the Network SSID and Password from secrets.py
# import the Spotify API keys from that file too
try:
    from secrets import WIFI_SSID, WIFI_PASSWORD
    if WIFI_SSID == "":
        raise ValueError("WIFI_SSID in 'secrets.py' is empty!")
    if WIFI_PASSWORD == "":
        raise ValueError("WIFI_PASSWORD in 'secrets.py' is empty!")
except ImportError:
    raise ImportError("'secrets.py' is missing from your Plasma 2350 W!")
except ValueError as e:
    print(e)

# Constants
API_URL = 'https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-C/standard-unit-rates/'

wlan = network.WLAN(network.STA_IF)


def network_connect():
    # Connect to the network specified in secrets.py
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    attempts = 0
    while wlan.isconnected() is False:
        print("Attempting connection to {}".format(WIFI_SSID))
        time.sleep(1)
        attempts += 1
        if attempts > 10:
            raise OSError('Unable to connect to wireless network. Check your WIFI_SSID and WIFI_PASSWORD and try again.')


# Start connection to the network
network_connect()

# Store the local IP address
ip_addr = wlan.ipconfig('addr4')[0]

# Let the user know the connection has been successful
# and display the current IP address of the Pimoroni Presto
print("Successfully connected to {}. Your Pimoroni Presto IP is: {}".format(WIFI_SSID, ip_addr))

# Set the correct time using the NTP service.
ntptime.settime()

# Setup for the Presto display
presto = Presto()
display = PicoGraphics(DISPLAY_PRESTO, buffer=memoryview(presto))
WIDTH, HEIGHT = display.get_bounds()

# Pico Vector
vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_BEST)

t = Transform()
vector.set_font("Roboto-Medium.af", 54)
vector.set_font_letter_spacing(100)
vector.set_font_word_spacing(100)
vector.set_transform(t)


# Couple of colours for use later
ORANGE = display.create_pen(255, 99, 71)
ORANGE_2 = display.create_pen(255, 99 + 50, 71 + 50)
ORANGE_3 = display.create_pen(255, 99 + 20, 71 + 20)
ORANGE_4 = display.create_pen(255, 99 + 70, 71 + 70)
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

MARGIN = 15

# Clear the screen and use blue as the background colour
display.set_pen(ORANGE)
display.clear()
display.set_pen(ORANGE_3)
display.text("Getting prices...", 10, 90 + 2, WIDTH, 4)
presto.update(display)
presto.update(display)

# Keep a record of the last time we updated.
# We only want to be requesting new information every half an hour.
last_updated = time.time()


def get_prices():

    try:
        # We only need the the first 6 elements covering the date and time
        t = time.localtime()[0:5]

        # Put that into a datetime object
        period_current = datetime.datetime(*t)
        period_next = period_current + datetime.timedelta(hours=1)
        period_last = period_current - datetime.timedelta(minutes=30)

        # Construct the time period to/from for our request later.
        request_string = (f"?period_from={period_last.year}-{period_last.month}-{period_last.day}T{period_last.hour}:{'00' if period_last.minute <= 29 else 30}Z"
                          f"&period_to={period_next.year}-{period_next.month}-{period_next.day}T{period_next.hour}:{'00' if period_next.minute <= 29 else '30'}Z")

        # Assemble our URL and make a request.
        request = requests.get(f"{API_URL}{request_string}")
        json = request.json()

        # Finally we return our 3 values
        return json['results'][0]['value_inc_vat'], json['results'][1]['value_inc_vat'], json['results'][2]['value_inc_vat']

    # if the above request fails, we want to handle the error and return values to keep the application running.
    except ValueError:
        return 0, 0, 0


# Get the prices on start up, after this we'll only check again at the top of the hour.
next_price, current_price, last_price = get_prices()


while True:

    # Clear the screen and use orange as the background colour
    display.set_pen(ORANGE)
    display.clear()

    # Draw a big orange circle that's lighter than the background
    display.set_pen(ORANGE_4)
    v = Polygon()
    v.circle(0, HEIGHT // 2, 190)
    vector.draw(v)

    # Check if it has been over half an hour since the last update
    # if it has, update the prices again.
    if time.time() - last_updated > 1800:
        next_price, current_price, last_price = get_prices()
        last_updated = time.time()

    # Draw the drop shadows and the main text for the last, current and next prices.
    vector.set_font_size(28)
    display.set_pen(ORANGE_2)
    vector.text("last:", MARGIN, 50)
    vector.text(f"{last_price}p", MARGIN, 70)

    vector.set_font_size(52)

    display.set_pen(BLACK)
    vector.text("Now:", MARGIN + 2, 120 + 2)
    vector.set_font_size(58)
    vector.text(f"{current_price}p", MARGIN + 2, 160 + 2)

    display.set_pen(WHITE)
    vector.set_font_size(52)
    vector.text("Now:", MARGIN, 120)
    vector.set_font_size(58)
    vector.text(f"{current_price}p", MARGIN, 160)

    vector.set_font_size(28)
    display.set_pen(ORANGE_3)
    vector.text("Next:", MARGIN, 195)
    vector.text(f"{next_price}p", MARGIN, 215)

    # Finally we update the screen with our changes :)
    presto.update(display)
