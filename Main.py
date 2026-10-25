# Scorpion - main program (Raspberry Pi Pico, MicroPython)
# Save on the Pico as "main.py" (all lowercase) so it runs at power-up.
#
# Current behavior: wait, calibrate the floor, then drive forward until
# the rover either hits the boundary tape or finds metal, then stop.

import time
from machine import Pin

from motordriver import movement
from reflectance_sensor import QTR8A

# ---------------------------------------------------------------- settings

METAL_PIN = 18          # LJ18A3-8 black wire (through the diode). NOT 14-17:
                        # those are the motor pins in motordriver.py.
FRONT_QTR_ADC = 27      # front QTR-8A mux output
START_DELAY_MS = 2000   # time to set the rover down and get hands clear
LOOP_MS = 2             # polling interval while driving

# ---------------------------------------------------------------- hardware

metal = Pin(METAL_PIN, Pin.IN, Pin.PULL_UP)
led = Pin("LED", Pin.OUT)
front = QTR8A(adc_pin=FRONT_QTR_ADC, name="front")


def metal_detected():
    # Active low. Require two low reads in a row so motor noise
    # doesn't cause a false trigger.
    if metal.value() == 0:
        time.sleep_ms(1)
        return metal.value() == 0
    return False


# ---------------------------------------------------------------- behaviors

def drive_until_event():
    # Drive forward until something happens. Returns "boundary" or "metal".
    # Tape is checked first: it's the safety condition, and the aluminum
    # tape may also set off the metal detector.
    movement("F")
    while True:
        if front.sees_tape():
            return "boundary"
        if metal_detected():
            return "metal"
        time.sleep_ms(LOOP_MS)


def main():
    movement("S")
    time.sleep_ms(START_DELAY_MS)
    front.calibrate_floor()        # rover must start on plain floor, not tape
    led.value(1)

    while True:
        event = drive_until_event()
        movement("S")
        print("Stopped:", event)

        if event == "metal":
            # TODO: read color -> grab with magnet, or reject and turn away
            pass
        else:
            # TODO: back up, random 100-170 degree turn away from the tape
            pass

        break   # remove once the two handlers above are written


try:
    main()
finally:
    movement("S")    # always stop the motors, even on Ctrl+C or a crash
    led.value(0)