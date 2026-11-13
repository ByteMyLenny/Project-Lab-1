from machine import Pin, mem32
from utime import sleep

MOTOR_L_LOW_1 = Pin(15, Pin.OUT)
MOTOR_L_LOW_2 = Pin(0, Pin.OUT)
MOTOR_L_HIGH_1 = Pin(14, Pin.OUT)
MOTOR_L_HIGH_2 = Pin(1,Pin.OUT)

MOTOR_R_HIGH_1 = Pin(15, Pin.OUT)
MOTOR_R_HIGH_2 = Pin(0, Pin.OUT)
MOTOR_R_LOW_1 = Pin(13, Pin.OUT)
MOTOR_R_LOW_2 = Pin(2,Pin.OUT)
LED = Pin("LED", Pin.OUT)

print("ON")
#MOTOR_L_LOW_1.value(1)
#MOTOR_L_LOW_2.value(2)
MOTOR_L_HIGH_1.value(1)
MOTOR_L_HIGH_2.value(1)
MOTOR_R_HIGH_1.value(1)
MOTOR_R_HIGH_2.value(1)
LED.value(1)
sleep(3)

MOTOR_L_LOW_1.value(1)
MOTOR_L_LOW_2.value(1)
MOTOR_R_LOW_1.value(1)
MOTOR_R_LOW_2.value(1)

sleep(3)
print("OFF")
MOTOR_L_LOW_1.value(0)
MOTOR_L_LOW_2.value(0)
MOTOR_L_HIGH_1.value(0)
MOTOR_L_HIGH_2.value(0)
MOTOR_R_LOW_1.value(0)
MOTOR_R_LOW_2.value(0)
LED.value(0)