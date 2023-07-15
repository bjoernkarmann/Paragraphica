## **📡 Initial RPI setup**

set up SD card with **Raspberry Pi Imager** and make sure it is able to connect to the internet fot the initial setup. Then ssh into the device:

```
ssh pi@raspberrypi.local
```

password is: paragraphica

if that does not work run the nmap on your routers ip: 
```
nmap -sn 192.168.1.1/24
```
Find the ip adress for your pi, then ssh using the ip adress directly:

```
ssh pi@192.168.1.175
```

if you have *key varification failed* error, simply reset it and try again: 
```
ssh-keygen -R 192.168.1.175
```

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
Save and exit.

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
Save and exit.

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

Find the line #DAEMON_CONF="" and replace it with:
```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```
Save and exit. 

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

Save and exit. 

The Raspberry Pi should now be set up to run a WiFi network on startup. However, we still need to create the ap0 interface on boot. For that, we need to add a line to /etc/rc.local:

```
sudo nano /etc/rc.local
```

Add this line before exit 0:
```
iw dev wlan0 interface add ap0 type __ap
```

Save and exit and reboot your Pi:
```
sudo reboot
```
You should be able to see "Paragraphica Connect" on your network list.

You can also check if wlan0 and ap0 are both on the list when running:
```
iwconfig
```

---
## **🚪 Install and Configure NoDogSplash**

Make sure you ssh back into your raspberrypi. Then install nessesarry packages: 

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
Edit the configure file with these parameters:
```
GatewayInterface ap0
GatewayAddress 192.168.50.1  
GatewayPort 2050
```
*note that some of the parameters may exisit and just need to be changed. 

Save and exit. 

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
you should be able to see "active" to insure a successful install: 
```
sudo systemctl status nodogsplash
```

---
## **💾 Clone and Update Git Repository**

If not already installed then make sure you have git installed: 
```
sudo apt update
sudo apt install git
```

Clone the Paragraphica-v2 repository to the root

```
cd
git clone https://github.com/bjoernkarmann/Paragraphica-v2.git
```

to update the git repository run: 
```
cd Paragraphica-v2
git pull
```

## **🚨 Prepare Project Requirements**

Install pip3
```
sudo apt-get install python3-pip
```
install flask through pip3
```
pip3 install flask
```

Now we can try run the wifi-connect.py to check if the captive portal appears when connecting to the network "Paragraphica Connect":
```
python3 wifi-connect.py
```
---
## **🥾 Setup Boot Script**

Untested!

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