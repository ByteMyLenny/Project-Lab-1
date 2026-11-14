from machine import Pin, time_pulse_us
from MotorDriver import movement
import Reflectance_Sensor as rs
import ColorSensor as cs
from Servo import set_angle, set_pulse
from utime import sleep
import sys
import select

electromagnet = Pin(8, Pin.OUT)

movement("F", 50)
sleep(5)
movement("S")