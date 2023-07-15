## **📡 Initial setup **

set up SD card with **Raspberry Pi Imager** and make sure it is able to connect to the internet fot the initial setup. Then ssh into the device:

```
ssh pi@raspberrypi.local
```

if that does not work run the nmap -sn 192.168.1.0/24 command and ssh intothe ip adress directly: 

---
## **📡 Setup WiFi Access Point**

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
---
## **💾 Clone and Update Git Repository**

Install git: 
```
sudo apt update
sudo apt install git
```

Clone the Paragraphica-v2 repository

```
git clone https://github.com/bjoernkarmann/Paragraphica-v2.git
```

to update the git repository run: 
```
cd Paragraphica-v2
git pull
```
---
## **🚪 Install and Configure NoDogSplash**

For this we will install NoDogSplash. First install nessesarry packages: 

```
sudo apt install git build-essential libssl-dev apache2-utils libmicrohttpd-dev
```

Clone the NoDogSplash repository: 
```
git clone https://github.com/nodogsplash/nodogsplash.git
```
Enter the nodogsplash directory:
```
cd nodogsplash
```
install
```
make
sudo make install
```
create the /etc/nodogsplash directory:
```
sudo mkdir /etc/nodogsplash
```
then copy the default nodogsplash.conf into that directory:
```
sudo cp /home/pi/nodogsplash/resources/nodogsplash.conf /etc/nodogsplash/
```
open the nodogsplash.conf in nano
```
sudo nano /etc/nodogsplash/nodogsplash.conf
```
Edit the conf file with these parameters:
```
GatewayInterface ap0
GatewayAddress 192.168.50.1  
GatewayPort 2050
```
set firefall settings:
```
sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
```
then:
```
sudo iptables -t nat -A PREROUTING -i ap0 -p tcp --dport 80 -j REDIRECT --to-port 2050
```
Restart **nodogsplash** to apply the changes:

```
sudo cp ~/nodogsplash/debian/nodogsplash.service /lib/systemd/system/
sudo systemctl enable nodogsplash.service 

sudo systemctl start nodogsplash.service 
```
---
## **🚨 Prepare Project Requirements**

Get pip3
```
sudo apt-get install python3-pip
```
install flask through pip3
```
pip3 install flask
```
---
## **🥾 Setup Boot Script**

Open the /etc/rc.local file in a text editor. You can use nano:
```
sudo nano /etc/rc.local
```
Add the following line before exit 0 in the file:
```
python3 /home/pi/Paragraphica-v2/wifi-connect.py &
```

Make your script executable by running:
```
sudo chmod +x /home/pi/Paragraphica-v2/wifi-connect.py
```