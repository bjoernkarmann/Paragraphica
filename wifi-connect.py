from flask import Flask, request, render_template 
import subprocess
import os
import time
import re
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

# Set up buttons GPIO pins
button1 = Button(2)
button2 = Button(3)
button3 = Button(4)
button4 = Button(17)

# Set up GPS
gpsd = gps(mode=WATCH_ENABLE)

# Read MCP3008 data from analouge potentialmeters
def read_channel(channel):
    adc = spiDials.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

options1 = ["one", "two", "tree", "four"]
options2 = ["Painting", "Photo", "Watercolor", "Illustration"]
options3 = ["1900", "1950", "1960", "1970"]

app = Flask(__name__)

def map_range(value, in_min, in_max, out_min, out_max):
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def get_ssids():
    try:
        result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], stdout=subprocess.PIPE)
        ssids = re.findall(r'ESSID:"(.*?)"', result.stdout.decode())
        return ssids
    except Exception as e:
        print(f"Pv2 Error scanning networks: {e}")

def check_wifi():
    result = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE)
    return result.stdout.strip() != b''

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
                launch_program()
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
    
def launch_program():
    subprocess.run(['python3', './main.py']) 

# ===========================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

# Top navigation bar
title = "WiFi Setup"  
status = "Page 1"

page = '1'

while True:
    # Read potentiometer data
    pot1 = read_channel(0)
    pot2 = read_channel(1)
    pot3 = read_channel(2)

    # Map potentiometer values to array indexes and select options
    opt1 = options1[map_range(pot1, 0, 1023, 0, len(options1)-1)]
    opt2 = options2[map_range(pot2, 0, 1023, 0, len(options2)-1)]
    opt3 = options3[map_range(pot3, 0, 1023, 0, len(options3)-1)]

    # Check buttons
    if button1.is_pressed:
        print("Left")
    if button2.is_pressed:
        print("Right")
    if button3.is_pressed:
        print("Select/Mode")
    if button4.is_pressed:
        print("Trigger")

    if page == '1':
    # Page 1 logic

    elif page == '2':  
        # Page 2 logic

    else:
        print("")
        # Page 3 logic