# Team.py
from machine import Pin
from utime import sleep_ms

COLORS = ("MAGENTA", "YELLOW", "CYAN")   # remote buttons 1, 2, 3 → 1, 2, 3 blinks
_color = None
_led = Pin("LED", Pin.OUT, value=0)

def set_color(color):
    global _color
    color = color.upper()
    if color not in COLORS:
        raise ValueError("Unknown team color: " + color)
    _color = color

def blink_color(on_ms=200, off_ms=200):
    """Blinks the onboard LED: 1 = MAGENTA, 2 = YELLOW, 3 = CYAN.
    One long blink if no team is set."""
    if _color is None:
        _led.value(1)
        sleep_ms(1000)
        _led.value(0)
        return
    for _ in range(COLORS.index(_color) + 1):
        _led.value(1)
        sleep_ms(on_ms)
        _led.value(0)
        sleep_ms(off_ms)

def get_color(blink=False):
    """Returns the team color (or None). blink=True also blinks the LED to show it."""
    if blink:
        blink_color()
    return _color