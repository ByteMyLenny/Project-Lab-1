from machine import Pin
import time

p = Pin(18, Pin.OUT, value=1)
print("GP18 is ON - take your readings. Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    p.off()
    print("GP18 off.")