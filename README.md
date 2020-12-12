# rpi_autodisplay
I have been looking into how to automatically adjust the brightness of the official 7" Raspberry Pi touchdisplay to the ambient brightness. This should behave similar to a smartphone or modern laptop screen and turn off the display when it is completely dark. So, if it is super bright in a room (in lux), then the brightness value (in %) should be accordingly high. If it is rather dark, then the display should also be dimmed. In addition, I would like to have a connection to openHAB and here to adjust the automatic brightness and also the display on and off. As a brightness sensor I will use the BH1750 sensor and as a software solution comes a Python script with the appropriate libraries to the course.

# Requirements
* Raspberry Pi (2, 3, 4)
* Raspberry Pi's official 7" touchdisplay
* BH1750 light sensor
* Raspbian installation
* python3
* python3 libraries 
* i2c bus
* optional: MQTT Broker and openHAB (only for `rpi_autodisplay-mqtt.py`)

```bash
raspi-config nonint do_i2c 0
apt install -y python3 python3-smbus i2c-tools python3-pip python3-systemd -y 
pip3 install --user adafruit-circuitpython-bh1750 rpi-backlight
```
# Installation
```bash
cd /usr/src/
git clone https://github.com/alaub81/rpi_autodisplay.git
cp rpi_autodisplay/*.py /usr/local/sbin/
cp rpi_autodisplay/display.service /etc/systemd/system/
chmod +x /usr/local/sbin/rpi_autodisplay*.py
```

# Configuration
## rpi_autodisplay.py
if you just like to use the stuff without MQTT you do not need to configure anything. Just enable the systemd service.
```bash
systemd daemon-reload
systemctl enable display.service
systemctl start display.service
```
## rpi_autodisplay-mqtt.py
If you like to use the mqtt version, you have to configure the MQTT connection in the `/usr/local/sbin/rpi_autodisplay-mqtt.py`:
```python3
# MQTT Config
broker = "FQDN / IP ADDRESS" # --> Broker FQDN or IP address
port = 8883 # --> MQTT Broker TCP Port (8883 for the TLS Port, 1883 for the standard Port)
publish_topic="home/attic/office" # --> in which topic you want to publish
clientid = "client-dp" # --> MQTT Client ID, should be unique.
hostname = "clientname" # --> In this topic the helping MQTT values are published (lux goes directly into the topic)
username = "mosquitto" # --> MQTT username, if authentication is used
password = "password" # --> MQTT password, if authentication is used
insecure = True # --> if using a self signed certificate
qos = 1 # --> MQTT QoS level (0, 1, 2) 
retain_message = True # --> publish as a retained mqtt message (True, False)
```
And you have to edit the `/etc/systemd/system/display.service`. Here you need to change the stuffe for the `rpi_autodisplay-mqtt.py`
```bash
...

# Starting after System is online and docker is running
# Only needed if MQTT is used
Wants=network-online.target
After=network-online.target
# Only needed if MQTT Broker is running in a Docker Container on the same Host
#After=docker.service
#After=docker.socket

...

# Command to execute when the service is started
# Without MQTT
#ExecStart=/usr/bin/python3 /usr/local/sbin/rpi_autodisplay.py
# Command to execute when the service is started
# With MQTT
ExecStart=/usr/bin/python3 /usr/local/sbin/rpi_autodisplay-mqtt.py

... 
```
now you could also enable and start the systemd service
```bash
systemd daemon-reload
systemctl enable display.service
systemctl start display.service
```

# Testing
Check if the service is runnig:
```bash
systemctl status display.service
```
Just test it with a flaslight and with covering the sensor with your hand. You should see the display changing its brightness and even going off and on.

# Whole Documentation of that Project:
More Informations here (Sorry, it's german, but just use your browsers transaltion tool): [Raspberry Pi Touchdisplay Helligkeit automatisch justieren](https://www.laub-home.de/wiki/Raspberry_Pi_Touchdisplay_Helligkeit_automatisch_justieren)

# Questions, Help, Feedback
if you have any questions, you need help, or just have feedback for my first project here, just let me know!
