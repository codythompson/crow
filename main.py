# https://github.com/adafruit/Adafruit-QT-Py-PCB/blob/master/Adafruit%20QT%20Py%20SAMD21%20pinout.pdf
import time
import busio
import board
import neopixel
import pwmio
from adafruit_motor import servo
import adafruit_mpr121

pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.brightness = 0.1

mode = 0
modeWasChanged = False

# create a PWMOut object on the control pin.
pwm = pwmio.PWMOut(board.A2, duty_cycle=0, frequency=50)
# create a PWMOut object on the control pin.
pwm2 = pwmio.PWMOut(board.A3, duty_cycle=0, frequency=50)
# This is an example for the Micro servo - TowerPro SG-92R: https://www.adafruit.com/product/169
legServo = servo.Servo(pwm, min_pulse=500, max_pulse=2400)
headServo = servo.Servo(pwm2, min_pulse=500, max_pulse=2400)

# capacitive touch / i2c setup
i2c = busio.I2C(board.SCL1, board.SDA1)
cap = adafruit_mpr121.MPR121(i2c)

settings = {
    "blink": 1,
    "servo": 1/60,
    "captest":1/30 
}

ticks = {
    "blink": time.monotonic(),
    "servo": time.monotonic(),
    "captest": time.monotonic()
}

# def min(a, b):
#     return a if a < b else b
def abs(val):
    return val if val >= 0 else -val

def getServo():
    if (mode == 0):
        return legServo
    elif (mode == 1):
        return headServo
    else:
        return legServo


# TODO split this out per servo - otherwise a mode switch will cause a jump to the previous servos position

movingTo = 0.5
current = 0.5
speed = 0.02

def tickServo():
    global movingTo, current, speed
    distance = current - movingTo
    if distance < 0:
        current += speed if speed < abs(distance) else -distance
    elif distance > 0:
        current -= speed if speed < distance else distance
    
    activeServo = getServo()
    if activeServo.fraction == None or abs(activeServo.fraction - current) > 0.001:
        activeServo.fraction = 0.15 + (current * (0.60 - 0.15)) # 1.0 and 0.15 are the max and min for crow safe operation - not in var to save mem

cap_mode_pin = 9
cap_pin_start = 3
def readTouches():
  global cap_pin_start,mode,modeWasChanged,movingTo

#   if cap.is_touched(cap_pin_start) and cap.is_touched(cap_pin_start+4):
  if cap.is_touched(cap_mode_pin):
    if not modeWasChanged:
        mode += 1
        mode = mode % 2
    modeWasChanged = True
    return
  else:
    modeWasChanged = False

  weight = 0.0
  touched_count = 0
  for i in range(cap_pin_start, cap_pin_start+5):
    if cap.is_touched(i):
      weight += i - (cap_pin_start+2)
      touched_count += 1
  if (touched_count > 0):
    sFraction = ((weight/touched_count)+2)/4
    if (movingTo != sFraction):
      movingTo=sFraction

# funks = {
#     "blink": (lambda now: pixels.fill(0xFF0000) if int(now % 2) == 1 else pixels.fill(0x00FFFF)),
#     "servo": (lambda now: tickServo()),
#     "captest": (lambda now: readTouches())
# }

def tick(key, now):
    global settings, ticks
    interval = settings[key]
    last = ticks[key]
    if now - last >= interval:
        ticks[key] = now
        return True
    else:
        return False

while True:
    now = time.monotonic()
    for key in settings:
        if (tick(key, now)):
            # funks[key](now)
            if (key == "blink"):
                if mode == 0:
                    pixels.fill(0x00FF80)
                elif mode == 1:
                    pixels.fill(0x8000FF)
                else:
                    pixels.fill(0xFF0000)
                pixels.show()
            elif (key == "servo"):
                tickServo()
            elif (key == "captest"):
                readTouches()

