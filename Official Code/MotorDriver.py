from machine import Pin, PWM, Timer
from utime import sleep, sleep_ms

SPEED = 7        # percent
DUTY = int(65535 * SPEED / 100)  # PWM uses 0–65535
FREQ = 200
TRIP_TIME_MS = 200      # must stay tripped this long to count
oc_count = 0
tripped = False

MOTOR_L_ORANGE_1 = PWM(Pin(15))
MOTOR_L_ORANGE_2 = PWM(Pin(0))
MOTOR_L_YELLOW_1 = PWM(Pin(14))
MOTOR_L_YELLOW_2 = PWM(Pin(1))

MOTOR_R_GRAY_1  = PWM(Pin(12))
MOTOR_R_GRAY_2  = PWM(Pin(3))
MOTOR_R_BLACK_1 = PWM(Pin(13))
MOTOR_R_BLACK_2 = PWM(Pin(2))


Overcurrent = Pin(16, Pin.IN, Pin.PULL_UP)

#HIGH LOW HIGH LOW
PINS = (MOTOR_L_YELLOW_1, MOTOR_L_YELLOW_2, MOTOR_L_ORANGE_1, MOTOR_L_ORANGE_2, MOTOR_R_GRAY_1, MOTOR_R_GRAY_2, MOTOR_R_BLACK_1, MOTOR_R_BLACK_2)



for pin in PINS:
    pin.freq(FREQ)               # 1 kHz
    pin.duty_u16(0)              # start off
# F / B 
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

def oc_check(timer):
    global oc_count, tripped
    if Overcurrent.value() == 0:
        oc_count += 1
        if oc_count >= TRIP_TIME_MS // 5 and not tripped:
            tripped = True
            stop()
            print("OVERCURRENT")
    else:
        oc_count = 0       # blip ended, reset

oc_timer = Timer(-1, period=5, mode=Timer.PERIODIC, callback=oc_check)

last_move = ("S", 0)

def movement(move, speed=SPEED):
    global last_move
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
            # kick: full power briefly so the motors break free
            for pin, state in zip(PINS, pattern):
                pin.duty_u16(65535 if state else 0)
            sleep_ms(50)
        # hold one pin of each pair, PWM the other at the requested speed
        for pin, state, hold in zip(PINS, pattern, HOLD):
            if not state:
                pin.duty_u16(0)
            elif hold:
                pin.duty_u16(65535)
            else:
                pin.duty_u16(duty)
    last_move = (move, speed)   

