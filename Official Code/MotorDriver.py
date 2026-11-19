from machine import Pin, PWM, Timer
from utime import sleep, sleep_ms, ticks_ms, ticks_diff

SPEED = 15        # percent
DUTY = int(65535 * SPEED / 100)  # PWM uses 0–65535
FREQ = 200
TRIP_TIME_MS = 200      # must stay tripped this long to count
KICK_SPEED = 40         # % power for the startup kick (was 100)
KICK_MS = 50            # how long the kick lasts
BLANK_MS = 250          # ignore overcurrent this long after each start / direction change
tripped = False

MOTOR_L_ORANGE_1 = PWM(Pin(15))
MOTOR_L_ORANGE_2 = PWM(Pin(0))
MOTOR_L_YELLOW_1 = PWM(Pin(14))
MOTOR_L_YELLOW_2 = PWM(Pin(1))

MOTOR_R_GRAY_1  = PWM(Pin(12))
MOTOR_R_GRAY_2  = PWM(Pin(3))
MOTOR_R_BLACK_1 = PWM(Pin(13))
MOTOR_R_BLACK_2 = PWM(Pin(2))

#HIGH LOW HIGH LOW
PINS = (MOTOR_L_YELLOW_1, MOTOR_L_YELLOW_2, MOTOR_L_ORANGE_1, MOTOR_L_ORANGE_2, MOTOR_R_GRAY_1, MOTOR_R_GRAY_2, MOTOR_R_BLACK_1, MOTOR_R_BLACK_2)

for pin in PINS:
    pin.freq(FREQ)
    pin.duty_u16(0)              # start off

# Per position in PINS: 1 = hold fully ON, 0 = PWM (sets the speed)
#        YELLOW   ORANGE   GRAY     BLACK
HOLD = (0, 1,    0, 1,    1, 0,    1, 0)
Patterns = { "F" : (1,1, 0,0, 1,1, 0,0),
             "B" : (0,0, 1,1, 0,0, 1,1),
             "L" : (0,0, 1,1, 1,1, 0,0),   # left back, right forward → spin left
             "R" : (1,1, 0,0, 0,0, 1,1),   # left forward, right back → spin right
             "S" : (0,0, 0,0, 0,0, 0,0)
            }

def stop():
    for pin in PINS:
        pin.duty_u16(0)

def _apply(pattern, duty):
    """Hold one pin of each pair fully on, PWM the other at `duty`."""
    for pin, state, hold in zip(PINS, pattern, HOLD):
        if not state:
            pin.duty_u16(0)
        elif hold:
            pin.duty_u16(65535)
        else:
            pin.duty_u16(duty)

# ---------- Overcurrent: one OCP board per side, active-low FAULT outputs ----------
OC_A = Pin(16, Pin.IN, Pin.PULL_UP)     # side A OCP (physical pin 21)
OC_B = Pin(27, Pin.IN, Pin.PULL_UP)     # side B OCP (physical pin 32)
oc_count_a = 0
oc_count_b = 0
tripped_side = None                     # "A" or "B" once tripped
blank_until = ticks_ms()                # ignore overcurrent until this time

def oc_check(timer):
    global oc_count_a, oc_count_b, tripped, tripped_side
    # Startup blanking: ignore the inrush right after the motors start or reverse
    if ticks_diff(blank_until, ticks_ms()) > 0:
        oc_count_a = 0
        oc_count_b = 0
        return
    # Leaky counters: count up while LOW, leak down while HIGH
    if OC_A.value() == 0:
        oc_count_a += 1
    elif oc_count_a > 0:
        oc_count_a -= 1
    if OC_B.value() == 0:
        oc_count_b += 1
    elif oc_count_b > 0:
        oc_count_b -= 1

    if not tripped:
        limit = TRIP_TIME_MS // 5
        if oc_count_a >= limit:
            tripped_side = "A"
        elif oc_count_b >= limit:
            tripped_side = "B"
        if tripped_side:
            tripped = True
            stop()
            print("OVERCURRENT on side", tripped_side)

oc_timer = Timer(-1, period=5, mode=Timer.PERIODIC, callback=oc_check)

# ---------- Driving ----------
last_move = ("S", 0)

def movement(move, speed=SPEED):
    global last_move, blank_until
    if tripped:
        stop()
        raise SystemExit
    if (move, speed) == last_move:
        return                    # already doing exactly this
    duty = int(65535 * speed / 100)
    direction_changed = move != last_move[0]
    if direction_changed:
        stop()
        if last_move[0] != "S":
            sleep_ms(150)         # let the motors slow down before switching
    pattern = Patterns[move]
    if move != "S":
        if direction_changed:
            # ignore the startup current spike for a moment
            blank_until = ticks_ms() + KICK_MS + BLANK_MS
            # soft kick so the motors break free without a huge spike
            kick = int(65535 * max(KICK_SPEED, speed) / 100)
            _apply(pattern, kick)
            sleep_ms(KICK_MS)
        _apply(pattern, duty)
    last_move = (move, speed)