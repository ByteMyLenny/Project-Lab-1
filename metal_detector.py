# LJ18A3-8 (NPN, normally open) inductive proximity sensor test
# Raspberry Pi Pico / Pico W - MicroPython
#
# Wiring:
#   Brown  -> +6 to 36 V supply (e.g. 12 V). The sensor needs at least 6 V.
#   Blue   -> supply GND AND Pico GND (grounds MUST be shared)
#   Black  -> diode -> GP15
#             (1N4148 or 1N4001: cathode/stripe toward the black wire,
#              anode toward GP15)
#
# The NPN output pulls to ground when metal is detected. The diode stops
# the supply voltage from ever reaching the 3.3 V-only Pico pin, and the
# Pico's internal pull-up holds the pin HIGH when nothing is detected.
#   No metal -> pin reads 1
#   Metal    -> pin reads 0

from machine import Pin
import time

SENSOR_PIN = 16

sensor = Pin(SENSOR_PIN, Pin.IN, Pin.PULL_UP)
led = Pin("LED", Pin.OUT)   # onboard LED (works on Pico and Pico W)

last_state = None
count = 0

print("LJ18A3-8 test running. Bring metal within ~8 mm of the sensor face.")

while True:
    detected = sensor.value() == 0   # active low
    led.value(detected)

    if detected != last_state:
        if detected:
            count += 1
            print("METAL DETECTED   (count = {})".format(count))
        else:
            print("clear")
        last_state = detected

    time.sleep_ms(20)   # simple debounce / polling interval