
set up SD card with **Raspberry Pi Imager**
ssh into the device via

```
ssh@raspberrypi.local
```

if that does not work run the nmap -sn 192.168.1.0/24 command and ssh intothe ip adress directly

## **Notes on setting up virtual access point**

Install the necessary software:

```
sudo apt update
sudo apt install dnsmasq hostapd
```

Then stop these services as we will configure them:
```
sudo systemctl stop dnsmasq
sudo systemctl stop hostapd
```

Create the virtual wireless interface by opening /etc/dhcpcd.conf:
```
sudo nano /etc/dhcpcd.conf
```
and then add the following lines to the end of the file: 
```
interface ap0
    static ip_address=192.168.50.1/24
    nohook wpa_supplicant
```

The next step is to configure the DHCP server (dnsmasq). Move the default configuration file and create a new one:
```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig  
sudo nano /etc/dnsmasq.conf
```
Then add the following to the new dnsmasq.conf:
```
interface=ap0
dhcp-range=192.168.50.50,192.168.50.150,255.255.255.0,12h
```
Now, set up the access point. Create the hostapd configuration file:
```
sudo nano /etc/hostapd/hostapd.conf
```
Add the following lines to this file:

```
interface=ap0
driver=nl80211
ssid=Paragraphica Connect
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=starmole
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

Modify /etc/default/hostapd to point to this configuration file:
```
sudo nano /etc/default/hostapd
```

Find the line #DAEMON_CONF="" and replace it with DAEMON_CONF="/etc/hostapd/hostapd.conf".

Enable and start hostapd and dnsmasq:
```
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

enable IP forwarding. Open /etc/sysctl.conf:

```
sudo nano /etc/sysctl.conf
```

And uncomment this line: **net.ipv4.ip_forward=1**

The Raspberry Pi should now be set up to run a WiFi network on startup. However, we still need to create the ap0 interface on boot. For that, we need to add a line to /etc/rc.local:

```
sudo nano /etc/rc.local
```

Add this line before exit 0:
```
iw dev wlan0 interface add ap0 type __ap
```

Now reboot your Pi:
```
sudo reboot
```

## **Bring in git files and set up boot script**