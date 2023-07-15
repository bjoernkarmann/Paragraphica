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
        return ssids
    except Exception as e:
        print(f"Pv2 Error scanning networks: {e}")

def check_wifi():
    result = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE)
    return result.stdout.strip() != b''

@app.route('/', methods=['GET', 'POST'])
def connect_wifi():
    error = None
    success = None
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
    os._exit(0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)