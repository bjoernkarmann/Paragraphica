from gpiozero import Button
from time import sleep
import spidev
import requests
from gps import gps, WATCH_ENABLE
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import pcd8544
from luma.core.render import canvas
import os

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

# Set up GPS
gpsd = gps(mode=WATCH_ENABLE)

# Define a function to read MCP3008 data
def read_channel(channel):
    adc = spiDials.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

def map_range(value, in_min, in_max, out_min, out_max):
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

options1 = ["0.1", "0.2", "0.3", "0.4"]
options2 = ["Painting", "Photo", "Watercolor", "Illustration"]
options3 = ["1900", "1950", "1960", "1970"]

while True:
    # Read potentiometer data
    pot1 = read_channel(0)
    pot2 = read_channel(1)
    pot3 = read_channel(2)

    # Map potentiometer values to array indexes and select options
    dial1 = options1[map_range(pot1, 0, 1023, 0, len(options1)-1)]
    dial2 = options2[map_range(pot2, 0, 1023, 0, len(options2)-1)]
    dial3 = options3[map_range(pot3, 0, 1023, 0, len(options3)-1)]

    print("Selected options:", dial1, dial2, dial3)

    # Display selected options
    with canvas(device) as draw:
        draw.text((0, 0), f"Options: {dial1}, {dial2}, {dial3}", fill="white")

    # Check buttons
    if button1.is_pressed:
        print("Button 1 - Left") # this button will navigate to the left 
    if button2.is_pressed:
        print("Button 2 - Right") # this button will navigate to the right
    if button3.is_pressed:
        print("Button 3 - Mode") # this button will change modes 
    if button4.is_pressed:
        print("Button 4 - Trigger") # this button will start the image process
        
        # Read GPS data
        gpsd.next()

        # URL for the API
        url = "http://92.242.187.242:5000/api"

        # Settings to send
        data = {
            "location": {"lat": gpsd.fix.latitude, "lon": gpsd.fix.longitude}, 
            "image_strength": dial1,
            "style": dial2, 
            "year": dial3
        }
        
        # Store the Paragraphica API key in the headers
        headers = {
            "X-API-KEY": "PLACE API KEY HERE"
        }

        # Send the POST request
        response = requests.post(url, json=data, headers=headers)

        # Check if request was successful
        if response.status_code == 200:
            print("Request successful")

            # Get the image file path from the response
            image_file_path = response.json().get('stability_image')
            description = response.json().get('description')
            status_report = response.json().get('status_report')

            # Download the image file
            with requests.get(image_file_path, stream=True) as r:
                r.raise_for_status()
                with open(os.path.join('images', os.path.basename(image_file_path)), 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Save the image to a static folder
            print(f"Image saved as {os.path.basename(image_file_path)}")
            print(f"Description = {description}")
            print(f"Status = {status_report}")

            # Send request to delete the image from the server
            delete_response = requests.delete(image_file_path, headers=headers)
            if delete_response.status_code == 200:
                print("Image deleted from the server")
            else:
                print("Failed to delete image from the server")

        else:
            print(f"Request failed with status code {response.status_code}")


    sleep(1)