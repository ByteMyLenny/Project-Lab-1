# ultrasonic.py
from machine import Pin
from utime import sleep_us, sleep_ms, ticks_us, ticks_diff
import random

# Placeholder pins; change to your actual wiring
TRIG       = Pin(21, Pin.OUT, value=0)   # shared by all 4 sensors
ECHO_FRONT = Pin(22, Pin.IN)             # front pair (diodes + 10k pull-up to 3.3 V)
ECHO_BACK  = Pin(17, Pin.IN)             # back pair  (diodes + 10k pull-up to 3.3 V)

STOP_DISTANCE_CM = 15    # anything closer than this counts as blocked
TIMEOUT_US = 30000       # no echo within 30 ms = nothing in range
PING_GAP_MS = 60         # sensors need ~60 ms between pings

def _wait_until_low(timeout_us=40000):
    """Make sure both echo lines are low before pinging (the last ping may still be finishing)."""
    start = ticks_us()
    while (ECHO_FRONT.value() or ECHO_BACK.value()) and ticks_diff(ticks_us(), start) < timeout_us:
        pass

def ping():
    """Fire all sensors once. Returns (front_cm, back_cm); None = nothing in range."""
    _wait_until_low()
    TRIG.value(1)
    sleep_us(10)
    TRIG.value(0)

    start = ticks_us()
    f_rise = f_fall = b_rise = b_fall = None
    while ticks_diff(ticks_us(), start) < TIMEOUT_US:
        now = ticks_us()
        f = ECHO_FRONT.value()
        b = ECHO_BACK.value()
        if f_rise is None:
            if f:
                f_rise = now
        elif f_fall is None and not f:
            f_fall = now
        if b_rise is None:
            if b:
                b_rise = now
        elif b_fall is None and not b:
            b_fall = now
        if f_fall is not None and b_fall is not None:
            break

    front = ticks_diff(f_fall, f_rise) / 58 if (f_fall is not None and f_rise is not None) else None
    back = ticks_diff(b_fall, b_rise) / 58 if (b_fall is not None and b_rise is not None) else None
    return front, back

def blocked():
    """One quick check. Returns (front_blocked, back_blocked) as True/False."""
    front, back = ping()
    f = front is not None and front < STOP_DISTANCE_CM
    b = back is not None and back < STOP_DISTANCE_CM
    return f, b

def confirmed(checks=3):
    """Pings several times. A side is True only if EVERY ping saw something close."""
    front_all = True
    back_all = True
    for _ in range(checks):
        sleep_ms(PING_GAP_MS)
        f, b = blocked()
        front_all = front_all and f
        back_all = back_all and b
        if not front_all and not back_all:
            return False, False       # cleared, so stop checking early
    return front_all, back_all

def random_turn(min_deg=90, max_deg=180):
    """Picks a random turn. Returns ("L" or "R", degrees)."""
    direction = "L" if random.randint(0, 1) == 0 else "R"
    return direction, random.randint(min_deg, max_deg)

if __name__ == "__main__":        # test: run this file directly
    while True:
        print(ping(), blocked())
        sleep_ms(200)