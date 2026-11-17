# IR_Receiver.py
from machine import Pin
from utime import ticks_ms, ticks_diff

PIN = 10                                  # TSOP38238 OUT pin (GP10 = physical pin 14)
_ir = Pin(PIN, Pin.IN, Pin.PULL_UP)

def detects(window_ms=200):
    """True if an IR signal is seen within window_ms, False if not.
    A real signal flickers LOW/HIGH; a pin stuck LOW the whole time counts as False."""
    saw_low = False
    saw_high = False
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < window_ms:
        if _ir.value() == 0:
            saw_low = True
        else:
            saw_high = True
        if saw_low and saw_high:
            return True                   # IR pulses seen, return early
    return False