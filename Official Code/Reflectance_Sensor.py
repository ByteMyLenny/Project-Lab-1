# reflectance_sensor.py
from machine import Pin, ADC
from utime import sleep, sleep_us

MUX_A = Pin(18, Pin.OUT, value=0)
MUX_B = Pin(19, Pin.OUT, value=0)
MUX_C = Pin(20, Pin.OUT, value=0)
MUX_OUT = ADC(26)            # CD4051 COM pin → GP26 (change if wired elsewhere)

TAPE_THRESHOLD = 20000       # set this with calibrate()
TAPE_VALUE_IS_LOWER_THAN_FLOOR = True           # True if tape return value is lower than floor

def select(ch):
    """Point the mux at sensor channel 0–7."""
    MUX_A.value(ch & 1)
    MUX_B.value((ch >> 1) & 1)
    MUX_C.value((ch >> 2) & 1)
    sleep_us(50)             # let the signal settle after switching

def read(ch, samples=4):
    """Averaged reading of one sensor (0–65535)."""
    select(ch)
    total = 0
    for _ in range(samples):
        total += MUX_OUT.read_u16()
    return total // samples

def read_all():
    return [read(ch) for ch in range(8)]

def is_tape(value):
    return value < TAPE_THRESHOLD if TAPE_VALUE_IS_LOWER_THAN_FLOOR else value > TAPE_THRESHOLD

def tape_sides():
    """Returns (left, right): True if that half of the sensor sees tape."""
    values = read_all()
    left = any(is_tape(v) for v in values[:4])
    right = any(is_tape(v) for v in values[4:])
    return left, right

def calibrate():
    """Prints readings over the floor and the tape, and a suggested threshold."""
    print("Hold sensor over FLOOR...")
    sleep(3)
    floor = sum(read_all()) // 8
    print("Hold sensor over TAPE...")
    sleep(3)
    tape = sum(read_all()) // 8
    print("Floor avg:", floor, " Tape avg:", tape)
    print("TAPE_THRESHOLD =", (floor + tape) // 2)
    print("TAPE_IS_LOW =", tape < floor)