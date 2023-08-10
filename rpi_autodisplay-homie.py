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
mqttclientid = "clientid-dp-homie"
clientid = "clientid-dp"
clientname = "Clientname Display"
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
powerswitchstate = "Null"
# if you like to raise all DISP_BRIGHTNESS
# set values betwenn 0.2 (lower brightness) and 2 (higher brightness)
# will be configured through MQTT Topic
# 1 will let it as it is
adjust = 1

### Functions
def publish(topic, payload):
  client.publish("homie/" + clientid + "/" + topic,payload,qos,retain_message)

def on_connect(client, userdata, flags, rc):
  print("MQTT Connection established, Returned code=",rc)
  client.subscribe("homie/" + clientid + "/display/#",qos)
  # homie client config
  publish("$state","init")
  publish("$homie","4.0")
  publish("$name",clientname)
  publish("$nodes","display,bh1750")
  # homie node configs
  publish("display/$name","RPI Display")
  publish("display/$type","Touchdisplay")
  publish("display/$properties","powerswitch,brightness,brightnessadjust")
  publish("display/powerswitch/$name","Display Power Switch")
  publish("display/powerswitch/$datatype","boolean")
  publish("display/powerswitch/$retained","true")
  publish("display/powerswitch/$settable","true")
  publish("display/brightness/$name","Display Brightness")
  publish("display/brightness/$datatype","float")
  publish("display/brightness/$unit","%")
  publish("display/brightness/$retained","true")
  publish("display/brightness/$settable","false")
  publish("display/brightnessadjust/$name","Display Brightness Adjustment")
  publish("display/brightnessadjust/$datatype","integer")
  publish("display/brightnessadjust/$unit","%")
  publish("display/brightnessadjust/$format","0:100")
  publish("display/brightnessadjust/$retained","true")
  publish("display/brightnessadjust/$settable","true")
  publish("bh1750/$name","BH1750 Sensor")
  publish("bh1750/$properties","illuminance")
  publish("bh1750/illuminance/$name","Illuminance")
  publish("bh1750/illuminance/$datatype","float")
  publish("bh1750/illuminance/$unit","lx")
  publish("bh1750/illuminance/$retained","true")
  publish("bh1750/illuminance/$settable","false")
  # homie state ready
  publish("$state","ready")

def on_message(client, userdata, message):
  global adjust
  global powerswitch
  global powerswitchstate
  global lastvalue
  #print("ALL Values", str(message.payload.decode("utf-8")))
  if "brightnessadjust/set" in message.topic:
    #print("Incoming adjust value", message.payload.decode("utf-8"))
    publish("display/brightnessadjust", message.payload.decode("utf-8"))
  if message.topic == ("homie/" + clientid + "/display/brightnessadjust"):
    #print("adjust value from state", message.payload.decode("utf-8"))
    adjust = (float(message.payload.decode("utf-8"))/100*2)
    #print("adjust: ",adjust)
    lastvalue = 0
  if "powerswitch/set" in message.topic:
    #print("MQTT Powerswitch from set:", str(message.payload.decode("utf-8")))
    powerswitch = (message.payload.decode("utf-8"))
  if message.topic == ("homie/" + clientid + "/display/powerswitch/powerstate"):
    #print("MQTT Powerswitch from state", message.payload.decode("utf-8"))
    powerswitchstate = (message.payload.decode("utf-8"))

def on_disconnect(client, userdata, rc):
  print("MQTT Connection disconnected, Returned code=",rc)

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
    publish("bh1750/illuminance", "%.2f" % lux)
    lastlux = lux

def backlightpower(state):
  backlight.power = state
  if state == True: strstate = "true"
  if state == False: strstate = "false"
  #print("STRSTATE to MQTT", strstate)
  publish("display/powerswitch", strstate)

def brightness(level):
  global dpb
  global lastvalue
  dpb = round(level * adjust)
  #print("dpb after adjustment:", dpb)
  #print("value to display:", (min(max((lux_level_1[1]), dpb), (lux_level_8[1]))))
  backlight.brightness = (min(max((lux_level_1[1]), dpb), (lux_level_8[1])))
  publish("display/brightness", "%.2f" % (min(max((lux_level_1[1]), dpb), (lux_level_8[1]))))
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
client.on_disconnect = on_disconnect

# Tell systemd that our service is ready
systemd.daemon.notify('READY=1')

# finaly the loop
while True:
  try:
    sensor()

    # Display ON/OFF
    backlightpowerstate = backlight.power
    #print("powerswitchstate: ", powerswitchstate)
    #print("powerswitch: ", powerswitch)
    if (powerswitch) == "Null" and (powerswitchstate) == "false":
      if backlightpowerstate == True:
        backlightpower(False)
        #publish("display/powerswitch/powerstate","false")
        #print("Display off")
      #time.sleep(1)
      #print("empty")
    elif (powerswitch) == "false":
      if backlightpowerstate == True:
        backlightpower(False)
        publish("display/powerswitch/powerstate","false")
        #print("Display off")
    elif (powerswitch) == "true" and backlightpowerstate == False and lux > (lux_level_1[0]):
      backlightpower(True)
      publish("display/powerswitch/powerstate","true")
      #print("Display auto")
    elif (powerswitch) == "true" and backlightpowerstate == False and lux < (lux_level_1[0]):
      backlightpower(True)
      time.sleep(ontime)
      powerswitch = "Null"
      backlightpower(False)
      #print("Overule Power for time", ontime)
    elif lux < (lux_level_1[0]) and backlightpowerstate == True:
      backlightpower(False)
      publish("display/powerswitch/powerstate","true")
      #print("Display auto aus", lux)
    elif lux > (lux_level_1[0]) and backlightpowerstate == False:
      backlightpower(True)
      publish("display/powerswitch/powerstate","true")
      #print("Display auto an", lux)

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
    publish("$state","disconnected")
    time.sleep(1)
    client.disconnect()
    client.loop_stop()
    exit (0)

  except :
    print("An Error accured ... ")
    time.sleep(3)
    continue

# At least close MQTT Connection
print("Script stopped")
publish("$state","disconnected")
time.sleep(1)
client.disconnect()
client.loop_stop()
