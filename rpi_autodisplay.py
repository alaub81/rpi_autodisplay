#!/usr/bin/python3
from rpi_backlight import Backlight
import board, adafruit_bh1750, systemd.daemon, time

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

### do the stuff
backlight = Backlight()
backlight.fade_duration = 0.5

# just give some used variables an initial value
lastvalue = 0
# if you like to raise all DISP_BRIGHTNESS
# set values betwenn 0.2 (lower brightness) and 2 (higher brightness)
# 1 will let it as it is
adjust = 1

# Tell systemd that our service is ready
print('Starting up Display Service ...')
systemd.daemon.notify('READY=1')

### Functions
def sensor():
  global lux
  i2c = board.I2C()
  sensor = adafruit_bh1750.BH1750(i2c)
  i = 0
  while sensor.lux <= lux_level_1[0] and i < 15:
    time.sleep(2)
    i += 1
    #print(i)
  lux = sensor.lux
  #print("%.2f Lux" % lux)

def backlightpower(state):
  backlight.power = state

def brightness(level):
  global dpb
  global lastvalue
  dpb = round(level * adjust)
  #print("dpb after adjustment:", dpb)
  #print("value to display:", (min(max((lux_level_1[1]), dpb), (lux_level_8[1]))))
  backlight.brightness = (min(max((lux_level_1[1]), dpb), (lux_level_8[1])))
  lastvalue = level

# running
# finaly the loop
while True:
  try:
    sensor()

    # Display ON/OFF
    if lux < (lux_level_1[0]) and backlight.power == True:
      backlightpower(False)
    elif lux > (lux_level_1[0]) and backlight.power == False:
      backlightpower(True)

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
    exit (0)

  except :
    print("An Error accured ... ")
    time.sleep(3)
    continue
