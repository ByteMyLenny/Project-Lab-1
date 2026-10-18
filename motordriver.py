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
    set_drive(n, 3)    

PINS = (GP14, GP15, GP16, GP17)

Patterns = { "F" : (1,0,0,1),
             "B" : (0,1,1,0),
             "S" : (0,0,0,0),
             "L" : (),
             "R" : ()
            }

def movement(move):
     for pin, state in zip(PINS, Patterns[move]):
        pin.value(state)

print("FORWARDS!")
movement("F")
sleep(5)
print("BACKWARDS!")
movement("B")
sleep(5)
movement("S")
sleep(5)

