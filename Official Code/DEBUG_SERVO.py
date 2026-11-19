# DEBUG_SERVO.py: For Basic Testing/Debugging. A playground.
import MotorDriver as driver, ColorSensor as cs, Servo as servo, Reflectance_Sensor as rs
from machine import Pin
from utime import sleep_ms, ticks_ms, ticks_diff


search_angle = 160
drop_angle = 30
grab_angle = 180
servo.set_angle(search_angle)