from machine import Pin, PWM
import time

servo = PWM(Pin(4))          # free slice, away from the motors
servo.freq(50)

def set_angle(deg, min_us=700, max_us=2450):
    deg = max(0, min(180, deg))                     # keep it in range
    pulse_us = min_us + (max_us - min_us) * deg / 180
    servo.duty_u16(int(pulse_us / 20000 * 65535))


def set_pulse(us):
    """Send a raw pulse width in microseconds, for finding the limits."""
    servo.duty_u16(int(us / 20000 * 65535))