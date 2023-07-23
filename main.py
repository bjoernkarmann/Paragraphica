import requests
import subprocess
import os
import re
import spidev
import time
import glob
from time import sleep
from gps import gps, WATCH_ENABLE
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.lcd.device import pcd8544
from luma.core.render import canvas
from gpiozero import Button
from flask import Flask, request, render_template 
from dotenv import load_dotenv

# take environment variables from .env.
load_dotenv()  

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

# Array of options to be selected by the dial. 
options1 = ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]
options2 = ["photography", ,"old analogue" "oil painting", "watercolor painting", "pencil sketch"]
options3 = ["1900", "1950", "1960", "1970", "1980", "1990", "2000", "2010"]

# Modes
current_mode = 0
modes = ["Mode1", "Mode2", "Mode3"]


#======================================================
# Funtions 

# Function to read dials connected to the MCP3008 data
def read_channel(channel):
    adc = spiDials.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

def map_range(value, in_min, in_max, out_min, out_max):
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# Function to get a list of wifi network names 
def get_ssids():
    try:
        result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], stdout=subprocess.PIPE)
        ssids = re.findall(r'ESSID:"(.*?)"', result.stdout.decode())
        return ssids
    except Exception as e:
        print(f"Pv2 Error scanning networks: {e}")

# Function to check the wifi status
def check_wifi():
    result = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE)
    return result.stdout.strip() != b''

# Function that draws the status bar
def display_status_bar(mode_name, wifi_status):
    with canvas(device) as draw:
        # Draw the gray bar
        draw.rectangle([(0, 0), (device.width, 16)], fill="gray")
        
        # Load a font (assuming DejaVuSans-Bold.ttf font is in your system)
        font = ImageFont.truetype("/static/fonts/SplineSansMono.ttf", 12)

        # Draw the mode name on the left
        draw.text((10, 2), mode_name, fill="black", font=font)
        
        # Draw the wifi status on the right
        draw.text((device.width - 50, 2), wifi_status, fill="black", font=font)

#======================================================
# Start Flask app so user can connect and insert their
# wifi information and connect Paragraphica to it.  

@app.route('/', methods=['GET', 'POST'])
def connect_wifi():
    error = ' '
    success = ' '
    ssids = get_ssids()
    
    # when user click on connect with ssid and password
    if request.method == 'POST':
        selected_ssid = request.form['ssid']
        wifi_password = request.form['password']
        
        if not selected_ssid:
            error = 'Please select a network'
        elif not wifi_password:
            error = 'WiFi password is required'
        else:
            print(f"Connecting to: {selected_ssid}")
            if connect_to_wifi(selected_ssid, wifi_password) and check_wifi():
                #launch_program()
                error = ' '
                success = 'Success!'
            else:
                error = 'Failed to connect'
                success = ' '

    # clean up data before sending it to the flask app
    ssid_options = [ssid for ssid in ssids if ssid and not ssid.startswith('\\x')]
    # start flask app
    return render_template('wifi-portal.html', ssid_options=ssid_options, error=error, success=success)   

def connect_to_wifi(ssid, password):
    print(f"Connecting to: " + ssid)
    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'a') as f:
        f.write(f'''

network={{
    ssid="{ssid}"
    psk="{password}" 
    key_mgmt=WPA-PSK
}}
        ''')

    subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])  
    print(f"Waiting to confirm connection...")
    time.sleep(10) # Wait for connection
    
    # check if wifi is connected
    result = subprocess.run(['ping', '-c', '4', '8.8.8.8'], stdout=subprocess.PIPE) 
    if result.returncode == 0:
        return True  # ping was successful, we have a connection
    else:
        return False  # ping failed, no connection

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

#======================================================
# Start the main app to handle the display, GPIO inputs
# and GPS module

# Top navigation bar
title = "WiFi Setup"  
status = "Page 1"

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

    # Check buttons
    if button1.is_pressed:
        print("Button 1 - Left") # this button will navigate to the left 
    if button2.is_pressed:
        print("Button 2 - Right") # this button will navigate to the right
    if button3.is_pressed:
        # Change current mode
        current_mode = (current_mode + 1) % 3
        print(f"Button 3 - Mode Changed to {modes[current_mode]}") # this button will change modes 

    #======================================================
    # The main photo trigger that will connect to the API 
    # and fetch the image and store it on the device. 
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
            "X-API-KEY": os.getenv('API_KEY')
        }

        # Send the POST request
        response = requests.post(url, json=data, headers=headers)

        # [TBD] Dsiplay waiting animation 

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

            # [TBD] SHOW IMAGE FOR 10 secounds on screen

        else:
            print(f"Request failed with status code {response.status_code}")
        
    #======================================================
    # Display modes and logic specific to the current mode
    if modes[current_mode] == "Mode1": 
        # Mode 1 is the default mode where GPIO and GPS settings
        # are shown. But if there is no wifi connected yet, then
        # it displays the set up wifi instructions.
        if check_wifi():
            # Wifi is connected, show text
            with canvas(device) as draw:
                draw.text((0, 0), f"Options: {dial1}, {dial2}, {dial3}", fill="white")
        else:
            # Wifi is not connected, show image from static folder
            # Replace 'path_to_your_image' with the path of the image you want to display
            image = Image.open('/static/images/wifi-connect.png')
            device.display(image.convert(device.mode))

    #======================================================
    elif modes[current_mode] == "Mode2":
        # Perform actions for Mode2
        # Path to the folder with images. Change it if necessary.
        image_folder_path = "/images/STILL NEEDS TESTING"

        # Get all .jpg images in the directory
        image_paths = glob.glob(os.path.join(image_folder_path, "*.png"))

        # Sort the images
        sorted_images = sorted(image_paths)

        # Index of the current image
        current_image_index = len(sorted_images) - 1  # Start with the most recent image

        # Check buttons
        if button1.is_pressed and current_image_index > 0:
            # Go to the previous image
            current_image_index -= 1

        if button2.is_pressed and current_image_index < len(sorted_images) - 1:
            # Go to the next image
            current_image_index += 1

        # Load and display the current image
        image = Image.open(sorted_images[current_image_index])
        device.display(image.convert(device.mode))

        # Display the current image number out of the total image count
        with canvas(device) as draw:
            draw.text((0, device.height - 10), f"Image {current_image_index + 1} of {len(sorted_images)}", fill="white")
    
    #======================================================
    elif modes[current_mode] == "Mode3":
        # Perform actions for Mode3
        pass

    # Display status bar after each mode
    wifi_status = "Connected" if check_wifi() else "Not Connected"
    display_status_bar(modes[current_mode], wifi_status)

    sleep(1)