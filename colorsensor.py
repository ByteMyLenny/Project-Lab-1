from machine import Pin
import machine
import time

# Set up the color-select pins
s0 = Pin(10, Pin.OUT)
s1 = Pin(11, Pin.OUT)
s2 = Pin(12, Pin.OUT)
s3 = Pin(13, Pin.OUT)
out = Pin(14, Pin.IN)

# Set frequency scaling to 20%
s0.value(1)
s1.value(0)

def read_color(s2_val, s3_val):
    s2.value(s2_val)
    s3.value(s3_val)
    time.sleep_ms(50)
    
    high_time = machine.time_pulse_us(out, 1, 100000)
    low_time = machine.time_pulse_us(out, 0, 100000)
    
    period = high_time + low_time
    if period <= 0:
        return 0
    return 1000000 / period

def classify(r, g, b):
    # Find the lowest of the three readings
    lowest = min(r, g, b)
    
    # How close the OTHER two are to each other matters -
    # a true secondary color has its two "high" channels roughly balanced
    tolerance = 0.35;
    if lowest == b and abs(r - g) < (max(r, g) * tolerance):
        return "YELLOW"
    elif lowest == g and abs(r - b) < (max(r, b) * tolerance):
        return "MAGENTA"
    elif lowest == r and abs(g - b) < (max(g, b) * tolerance):
        return "CYAN"
    else:
        return "Not confidently magenta, yellow, or cyan"

while True:
    red = read_color(0, 0)
    green = read_color(1, 1)
    blue = read_color(0, 1)
    
    result = classify(red, green, blue)
    
    print(f"R:{red:.0f} G:{green:.0f} B:{blue:.0f}  ->  {result}")
    time.sleep(0.5)