from machine import Pin
from utime import sleep

magnet = Pin(28, Pin.OUT)

magnet.value(1)
print("Magnet ON")
sleep(3)
magnet.value(0)
print("Magnet OFF")