#!/usr/bin/python3
from rpi_backlight import Backlight
import board, adafruit_bh1750, systemd.daemon, time
import paho.mqtt.client as mqtt, ssl

### set the variables
# Switch levels for brightness
# lux value (lux), brightness value (%)
lux_level_1 = 0.1, 25
lux_level_2 = 20, 35
lux_level_3 = 100, 45
lux_level_4 = 200, 55
lux_level_5 = 300, 65
lux_level_6 = 450, 75
lux_level_7 = 600, 85
lux_level_8 = 800, 100
"""
# my recommended values:
lux_level_1 = 0.1, 40
lux_level_2 = 20, 45
lux_level_3 = 100, 50
lux_level_4 = 200, 75
lux_level_5 = 300, 85
lux_level_6 = 450, 90
lux_level_7 = 600, 95
lux_level_8 = 800, 100
"""
# MQTT Config
broker = "FQDN / IP ADDRESS"
port = 8883
publish_topic="home/attic/office"
clientid = "client-dp"
hostname = "clientname"
username = "mosquitto"
password = "password"
insecure = True
qos = 1
retain_message = True
# Retry to connect to mqtt broker
mqttretry = 5
# time in seconds how long display will be on, if it is auto off
ontime = 30

### do the stuff
print('Starting up Display Service ...')
backlight = Backlight()
backlight.fade_duration = 0.75

# just give some used variables an initial value
lastvalue = 0
lastlux = 0
powerswitch = "Null"
# if you like to raise all DISP_BRIGHTNESS
# set values betwenn 0.2 (lower brightness) and 2 (higher brightness)
# will be configured through MQTT Topic
# 1 will let it as it is
adjust = 1

### Functions
def publish(topic, payload):
  client.publish(publish_topic + "/" + topic,payload,qos,retain_message)

def on_connect(client, userdata, flags, rc):
  print("MQTT Connection established, Returned code=",rc)
  client.subscribe([(publish_topic + "/" + hostname + "/dp_brightness_adjust", qos),\
    (publish_topic + "/" + hostname + "/dp_power_switch", qos)])

def on_message(client, userdata, message):
  global adjust
  global powerswitch
  global lastvalue
  if "dp_brightness_adjust" in message.topic:
    #print("adjust value", str(message.payload.decode("utf-8")))
    adjust = float(message.payload.decode("utf-8"))
    lastvalue = 0
  if "dp_power_switch" in message.topic:
    #print("MQTT power payload:", str(message.payload.decode("utf-8")))
    powerswitch = (str(message.payload.decode("utf-8")).split(","))
    #print("split wert 1", powerswitch[0])

def sensor():
  global lux
  global lastlux
  i2c = board.I2C()
  sensor = adafruit_bh1750.BH1750(i2c)
  i = 0
  while sensor.lux <= lux_level_1[0] and i < 15:
    time.sleep(2)
    i += 1
    #print(i)  
  lux = sensor.lux
  if ("%.0f" % lastlux) != ("%.0f" % lux) or lux <= 1:
   publish("lux", "%.2f" % lux)
   lastlux = lux

def backlightpower(state):
  backlight.power = state
  if state == True: strstate = "On"
  if state == False: strstate = "Off"
  #print("STRSTATE to MQTT", strstate)
  publish(hostname + "/dp_power_switch", strstate)

def brightness(level):
  global dpb
  global lastvalue
  dpb = round(level * adjust)
  #print("dpb after adjustment:", dpb)
  #print("value to display:", (min(max((lux_level_1[1]), dpb), (lux_level_8[1]))))
  backlight.brightness = (min(max((lux_level_1[1]), dpb), (lux_level_8[1])))
  publish(hostname + "/dp_brightness_level", "%.2f" % (min(max((lux_level_1[1]), dpb), (lux_level_8[1]))))
  lastvalue = level

# running
#MQTT Connection
mqttattempts = 0
while mqttattempts < mqttretry:
  try:
    client=mqtt.Client(clientid)
    client.username_pw_set(username, password)
    client.tls_set(cert_reqs=ssl.CERT_NONE) #no client certificate needed
    client.tls_insecure_set(insecure)
    client.connect(broker, port)
    client.loop_start()
    mqttattempts = mqttretry
  except :
    print("Could not establish MQTT Connection! Try again " + str(mqttretry - mqttattempts) + "x times")
    mqttattempts += 1
    if mqttattempts == mqttretry:
      print("Could not connect to MQTT Broker! exit...")
      exit (0)
    time.sleep(5)

# MQTT Subscription
client.on_message = on_message
client.on_connect = on_connect

# Tell systemd that our service is ready
systemd.daemon.notify('READY=1')

# finaly the loop
while True:
  try:
    sensor()

    # Display ON/OFF
    if (powerswitch[0]) == "openHAB" and (powerswitch[1]) == "Off":
      if backlight.power == True:
        backlight.power = False
        #print("off")
    elif (powerswitch[0]) == "openHAB" and (powerswitch[1]) == "On" and lux > (lux_level_1[0]):
      backlightpower(True)
      #print("Display auto")
    elif (powerswitch[0]) == "openHAB" and (powerswitch[1]) == "On" and lux < (lux_level_1[0]):
      backlight.power = True
      time.sleep(ontime)
      backlightpower(True)
      #print("Overule Power for time", ontime)
    elif lux < (lux_level_1[0]) and backlight.power == True:
      backlightpower(False)
      #print("auto aus", lux)
    elif lux > (lux_level_1[0]) and backlight.power == False:
      backlightpower(True)
      #print("auto an", lux)

    # set lux levels to brightness levels (incl. adjust value) if backlight is on
    if backlight.power == True:
      if (lux_level_1[0]) <= lux < (lux_level_2[0]) and lastvalue != (lux_level_1[1]):
        brightness(lux_level_1[1])
      if (lux_level_2[0]) <= lux < (lux_level_3[0]) and lastvalue != (lux_level_2[1]):
        brightness(lux_level_2[1])
      if (lux_level_3[0]) <= lux < (lux_level_4[0]) and lastvalue != (lux_level_3[1]):
        brightness(lux_level_3[1])
      if (lux_level_4[0]) <= lux < (lux_level_5[0]) and lastvalue != (lux_level_4[1]):
        brightness(lux_level_4[1])
      if (lux_level_5[0]) <= lux < (lux_level_6[0]) and lastvalue != (lux_level_5[1]):
        brightness(lux_level_5[1])
      if (lux_level_6[0]) <= lux < (lux_level_7[0]) and lastvalue != (lux_level_6[1]):
        brightness(lux_level_6[1])
      if (lux_level_7[0]) <= lux < (lux_level_8[0]) and lastvalue != (lux_level_7[1]):
        brightness(lux_level_7[1])
      if lux >= (lux_level_8[0]) and lastvalue != (lux_level_8[1]):
        brightness(lux_level_8[1])

  except KeyboardInterrupt:
    print("Goodbye!")
    # At least close MQTT Connection
    client.disconnect()
    client.loop_stop()
    exit (0)

  except :
    print("An Error accured ... ")
    time.sleep(3)
    continue

# At least close MQTT Connection
client.disconnect()
client.loop_stop()
