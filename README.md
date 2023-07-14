# Easy set up


# Mannual set up 

This mannual guide will set up a Raspberry Pi for the Paragraphica camera shield v2.1.

## Prerequisites

- A Raspberry Pi with WiFi capabilities
- Python 3 installed

## 1. Setup Raspberry Pi Zero

log into SSH using the terminal: 

```
ssh pi@raspberrypi.local
```
username: pi
password: paragraphica

```
sudo apt-get update
sudo apt-get install hostapd dnsmasq git python3-pip libmicrohttpd-dev build-essential
```



## 2. Setup Wifi connect

First we got to set up the wifi-connect.py on boot. We want a WiFi hotspot that provides a web interface for users to connect it to a WiFi network. 

### **2.1 Install necessary packages**

```
sudo pip3 install flask
```

```
git clone https://github.com/bjoernkarmann/Paragraphica-v2.git
```

### **2.2 Configure nodogsplash**
This will enable a captive portal to appear when the user logs into the network

pull nodogsplash from github
```
cd ~
git clone https://github.com/nodogsplash/nodogsplash.git
```

go to the nodogsplash folder and isntall it
```
cd ~/nodogsplash
make
sudo make install
```

open the nodogsplash.conf in nano
```
sudo nano /etc/nodogsplash/nodogsplash.conf
```

In edit mode change the RedirectURL to the IP of the raspberry pi: `RedirectURL http://192.168.0.1`. Save the configuration file and exit the text editor. If you're using nano, you can do this by pressing **Ctrl+X**, then **Y**, then **Enter**.

Restart **nodogsplash** to apply the changes:


```
sudo cp ~/nodogsplash/debian/nodogsplash.service /lib/systemd/system/
sudo systemctl enable nodogsplash.service 

sudo systemctl start nodogsplash.service 
```

### **2.3 Configure hostapd**

Edit the /etc/hostapd/hostapd.conf file to set up the WiFi hotspot:

```
sudo nano /etc/hostapd/hostapd.conf
```

Add the following configuration to the hostbad file:

```
interface=wlan0
driver=nl80211
ssid=paragraphica-connect
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
```

### **2.4 Setup the Python script to run at boot**

Create a new systemd service file:

```
sudo nano /etc/systemd/system/wifi-connect.service
```

Add the following content to the service file, replacing `/path/to/your/wifi-connect.py` with the actual path to your Python script:

```
[Unit]
Description=WiFi Connect
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/wifi-connect.py
WorkingDirectory=/path/to/your/
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable the service to start at boot:

```
sudo systemctl enable wifi-connect.service
```

Start the service:
```
sudo systemctl start wifi-connect.service
```


After setting up, the Raspberry Pi will broadcast a WiFi hotspot named `Paragraphica Connect`. Connect to this hotspot and navigate to the Raspberry Pi's IP address in a web browser to access the web interface. From there, you can select a WiFi network and enter the password to connect the Raspberry Pi to that network.