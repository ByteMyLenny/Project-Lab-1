from machine import Pin, PWM
import time

servo = PWM(Pin(15))
servo.freq(50)

def set_angle(deg, min_us=500, max_us=2500):
    pulse_us = min_us + (max_us - min_us) * deg / 180
    servo.duty_u16(int(pulse_us / 20000 * 65535))

