from machine import Pin, mem32
from utime import sleep

def set_drive(gpio, level):            # 0=2mA, 1=4mA, 2=8mA, 3=12mA
    addr = 0x4001C000 + 4 + 4 * gpio   # this pin's pad control register
    mem32[addr] = (mem32[addr] & ~(0b11 << 4)) | (level << 4)

GP14 = Pin(14, Pin.OUT)
GP15 = Pin(15, Pin.OUT)
GP16 = Pin(16, Pin.OUT)
GP17 = Pin(17, Pin.OUT)

for n in (14, 15, 16, 17):
    set_drive(n, 0)    

#HIGH LOW HIGH LOW
PINS = (GP14, GP15, GP17, GP16)

# F / B 
Patterns = { "F" : (1,0,  1,0),
             "B" : (0,1,  0,1),
             "L" : (0,1,  1,0),
             "R" : (1,0,  0,1),
             "S" : (0,0,  0,0)
            }

def movement(move):
     for pin, state in zip(PINS, Patterns[move]):
        pin.value(state)

