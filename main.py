from gpiozero import Button
from time import sleep
import spidev
import requests
from gps import gps, WATCH_ENABLE
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import pcd8544
from luma.core.render import canvas

# Set up SPI for dials
spiDials = spidev.SpiDev()
spiDials.open(0,1) # Open SPI bus 0, device 1
spiDials.max_speed_hz = 1350000

# Set up SPI for display
spiDisplay = spi(port=0, device=0)
device = pcd8544(spiDisplay)

# Set up buttons
button1 = Button(2)
button2 = Button(3)
button3 = Button(4)
button4 = Button(17)
button5 = Button(27)

# Set up GPS
gpsd = gps(mode=WATCH_ENABLE)

# Define a function to read MCP3008 data
def read_channel(channel):
    adc = spiDials.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

def map_range(value, in_min, in_max, out_min, out_max):
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

options1 = ["one", "two", "tree", "four"]
options2 = ["Painting", "Photo", "Watercolor", "Illustration"]
options3 = ["1900", "1950", "1960", "1970"]

while True:
    # Read potentiometer data
    pot1 = read_channel(0)
    pot2 = read_channel(1)
    pot3 = read_channel(2)

    # Map potentiometer values to array indexes and select options
    opt1 = options1[map_range(pot1, 0, 1023, 0, len(options1)-1)]
    opt2 = options2[map_range(pot2, 0, 1023, 0, len(options2)-1)]
    opt3 = options3[map_range(pot3, 0, 1023, 0, len(options3)-1)]

    print("Selected options:", opt1, opt2, opt3)

    # Display selected options
    with canvas(device) as draw:
        draw.text((0, 0), f"Options: {opt1}, {opt2}, {opt3}", fill="white")
        
    # Check buttons
    if button1.is_pressed:
        print("Button 1 pressed")
    if button2.is_pressed:
        print("Button 2 pressed")
    if button3.is_pressed:
        print("Button 3 pressed")
    if button4.is_pressed:
        print("Button 4 pressed")

    if button5.is_pressed:
        print("Button 5 pressed")
        
        # Read GPS data
        gpsd.next()
        print("GPS data:", gpsd.fix.latitude, gpsd.fix.longitude)

        # Make a GET request
        response = requests.get('http://example.com')
        print("Response from server:", response.text)


    sleep(1)