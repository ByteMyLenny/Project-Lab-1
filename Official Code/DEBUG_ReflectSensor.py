import Reflectance_Sensor as rs
from machine import Pin, PWM
from utime import sleep_ms


while True:
    print(rs.read_all())
    sleep_ms(1000)