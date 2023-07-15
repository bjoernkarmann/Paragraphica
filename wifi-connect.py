from flask import Flask, request, render_template 
import subprocess
import os
import time
import re

app = Flask(__name__)

def get_ssids():
    try:
        result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], stdout=subprocess.PIPE)
        ssids = re.findall(r'ESSID:"(.*?)"', result.stdout.decode())
        print(f"Pv2 Scanned networks")
        return ssids
    except Exception as e:
        print(f"Pv2 Error scanning networks: {e}")

def check_wifi():
    result = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE)
    return result.stdout.strip() != b''

@app.route('/', methods=['GET', 'POST'])
def connect_wifi():
    error = None
    ssids = get_ssids()
    
    # when user click on connect with ssid and password
    if request.method == 'POST':
        selected_ssid = request.form['ssid']
        wifi_password = request.form['password']
        
        if not selected_ssid:
            print(f"Pv2 select a network")
            error = 'Please select a network'
        elif not wifi_password:
            print(f"Pv2 password required")
            error = 'WiFi password is required'
        else:
            connect_to_wifi(selected_ssid, wifi_password)
            if check_wifi():
                launch_program()
                print(f"Success! Program launched")
                return 'Success! Program launched'
            else:
                error = 'Failed to connect'

    return render_template('wifi-portal.html', ssids=ssids, error=error)   

def connect_to_wifi(ssid, password):
    print(f"Pv2 Connecting to: " + ssid)
    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
        f.write(f'''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev    
update_config=1
country=US

network={{
    ssid="{ssid}"
    psk="{password}" 
    key_mgmt=WPA-PSK
}}
        ''')

    subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])  
    time.sleep(10) # Wait for connection
    
def launch_program():
    subprocess.run(['python3', './main.py']) 
    os._exit(0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)