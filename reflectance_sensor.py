# Pololu QTR-8A analog reflectance sensor arrays (Raspberry Pi Pico, MicroPython)
# Detects aluminum tape on the floor.
#
# Each sensor outputs a voltage: LOW when lots of IR bounces back (shiny
# aluminum tape reads lowest), HIGH when little does (dark floor). Power the
# board from 3.3 V (short the 3.3 V jumper) so the outputs stay under 3.3 V.
#
# The Pico only has 3 usable ADC pins (GP26, GP27, GP28), so each array goes
# through its own 74HC4051 / CD4051 8-channel analog mux. All the muxes
# share the same 3 select pins; each mux output gets its own ADC pin.
#
# Wiring (per array):
#   QTR VCC -> 3V3 OUT (physical pin 36)       QTR GND -> GND
#   QTR 1..8 -> mux Y0..Y7
#   mux Z    -> its own ADC pin: GP27 (pin 32) or GP28 (pin 34)
#   mux S0 S1 S2 -> GP2 GP3 GP4 (physical pins 4, 5, 6), shared by every mux
#   mux VCC -> 3V3, mux GND, VEE and E (enable) -> GND
#
# Without a mux, wire up to 3 sensors straight to ADC pins instead:
#   QTR8A(adc_pin=(27, 28), mux_select=None)
#
# Use it from another file:
#     from reflectance_sensor import QTR8A, any_tape
#
#     front = QTR8A(adc_pin=27, name="front")
#     rear  = QTR8A(adc_pin=28, name="rear")
#     front.calibrate_floor()      # optional: hold both arrays over plain floor
#     rear.calibrate_floor()
#
#     while True:
#         if any_tape(front, rear):        # True if ANY sensor sees tape
#             ...
#         if front.sees_tape():            # just one array
#             print(front.tape_sensors())  # which sensors, e.g. [3, 4]
#
# Or run this file directly to see live readings and pick a threshold.

import time
from machine import Pin, ADC

# Raw reading (0-65535) below which a sensor counts as "on tape" if you
# don't run calibrate_floor(). Run this file to see your actual numbers.
DEFAULT_THRESHOLD = 15000


class QTR8A:
    def __init__(self, adc_pin=27, mux_select=(2, 3, 4), sensors=8,
                 threshold=DEFAULT_THRESHOLD, name="qtr"):
        # adc_pin: the mux output's ADC pin, or with mux_select=None a tuple
        # of ADC pins, one per sensor (sensor 1 first).
        # sensors: how many mux channels are wired (sensor 1 on Y0, ...).
        self.name = name
        if mux_select:
            self.adc = ADC(Pin(adc_pin))
            self.select = [Pin(n, Pin.OUT, value=0) for n in mux_select]
            self.count = sensors
        else:
            pins = adc_pin if isinstance(adc_pin, (tuple, list)) else (adc_pin,)
            self.adcs = [ADC(Pin(n)) for n in pins]
            self.select = None
            self.count = len(pins)
        self.thresholds = [threshold] * self.count

    def _read_channel(self, i):
        if not self.select:
            return self.adcs[i].read_u16()
        for bit, p in enumerate(self.select):
            p.value((i >> bit) & 1)
        time.sleep_us(10)           # let the mux output settle
        self.adc.read_u16()         # throw away the first sample after switching
        return self.adc.read_u16()

    def read(self):
        # One raw value per sensor, 0 (very reflective) .. 65535 (very dark).
        return [self._read_channel(i) for i in range(self.count)]

    def calibrate_floor(self, margin=0.5, samples=20):
        # Hold the array over plain floor (no tape) while this runs. Each
        # sensor's threshold becomes margin x its floor reading, so tape has
        # to read at least that much brighter than the floor to count.
        totals = [0] * self.count
        for _ in range(samples):
            for i, v in enumerate(self.read()):
                totals[i] += v
            time.sleep_ms(5)
        self.thresholds = [int(t / samples * margin) for t in totals]
        print("[{}] floor thresholds: {}".format(self.name, self.thresholds))

    def tape_sensors(self):
        # Sensor numbers (1-8) currently over tape, e.g. [3, 4]. Empty if none.
        return [i + 1 for i, v in enumerate(self.read()) if v < self.thresholds[i]]

    def sees_tape(self):
        # True if any sensor in this array is over tape.
        for i in range(self.count):
            if self._read_channel(i) < self.thresholds[i]:
                return True
        return False


def any_tape(*arrays):
    # True if any sensor on any of the given arrays is over tape.
    return any(a.sees_tape() for a in arrays)


# ---------------------------------------------------------------- standalone

if __name__ == "__main__":
    qtr = QTR8A()
    print("QTR-8A on GP27 via mux (select GP2-GP4).")
    print("Raw values: low = reflective (tape), high = dark. # = tape.")
    print("Move it over floor and tape to check the threshold. Ctrl+C to stop.\n")
    try:
        while True:
            values = qtr.read()
            bar = "".join("#" if v < t else "." for v, t in zip(values, qtr.thresholds))
            print(bar, " ".join("{:5d}".format(v) for v in values))
            time.sleep_ms(200)
    except KeyboardInterrupt:
        print("\nStopped.")
