# reflectance_sensor.py
from machine import Pin, ADC
from utime import sleep, sleep_us

MUX_A = Pin(18, Pin.OUT, value=0)
MUX_B = Pin(19, Pin.OUT, value=0)
MUX_C = Pin(20, Pin.OUT, value=0)
MUX_OUT = ADC(26)            # CD4051 COM pin → GP26 (physical pin 31)

THRESHOLDS = [20000] * 8                 # one per sensor; set with calibrate()
TAPE_VALUE_IS_LOWER_THAN_FLOOR = True    # True if tape reads lower than floor

def select(ch):
    """Point the mux at sensor channel 0–7."""
    MUX_A.value(ch & 1)
    MUX_B.value((ch >> 1) & 1)
    MUX_C.value((ch >> 2) & 1)
    sleep_us(50)             # let the signal settle after switching

def read(ch, samples=4):
    """Averaged reading of one sensor (0–65535)."""
    select(ch)
    MUX_OUT.read_u16()       # throw away the first reading after switching
    total = 0
    for _ in range(samples):
        total += MUX_OUT.read_u16()
    return total // samples

def read_all():
    return [read(ch) for ch in range(8)]

def is_tape(value, ch):
    if TAPE_VALUE_IS_LOWER_THAN_FLOOR:
        return value < THRESHOLDS[ch]
    return value > THRESHOLDS[ch]

def tape_sides():
    """Returns (left, right): True if that half of the sensor sees tape."""
    values = read_all()
    hits = [is_tape(v, ch) for ch, v in enumerate(values)]
    return any(hits[:4]), any(hits[4:])

def calibrate():
    """Prints per-sensor readings over floor and tape, plus values to copy in."""
    print("Hold sensor over FLOOR...")
    sleep(3)
    floor = read_all()
    print("Hold sensor over TAPE...")
    sleep(3)
    tape = read_all()
    print("Floor:", floor)
    print("Tape: ", tape)
    print("THRESHOLDS =", [(f + t) // 2 for f, t in zip(floor, tape)])
    print("TAPE_VALUE_IS_LOWER_THAN_FLOOR =", sum(tape) < sum(floor))