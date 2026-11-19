# main.py
import IR_Receiver as irr, ProximitySensors as ps, ColorSensor as cs, MotorDriver as driver
import Servo as servo, Reflectance_Sensor as rs, Team, Setup
from utime import sleep_ms, ticks_ms, ticks_diff
from machine import Pin

LED = Pin("LED", Pin.OUT, value=0)
electromagnet = Pin(28, Pin.OUT, value=0)

##INITIAL SETUP##
Setup.calibrate_tape()
sleep_ms(5000)
Setup.calibrate_beacons()
servo.set_angle(175)
Setup.run(team_timeout_s=30)   # pick team with the remote, then press START
print("Playing as", Team.get_color())

##Initialize Factors##
ir = irr.IRReceiver(pin=10)
if Team.get_color() is None:
    print("WARNING: no team selected")
if not ir.codes:
    print("WARNING: no beacons calibrated; run Setup.calibrate_beacons()")
search_mode = 175
grab_mode = 180
bin_deposit_mode_initial = 30
bin_deposit_mode_final = 45

DRIVE_SPEED = driver.SPEED      # searching / homing speed (%)
TURN_SPEED = driver.SPEED + 5      # spin-in-place speed (%); raise if turns stall
DEG_PER_SEC = 180               # MEASURE THIS: degrees the rover spins per second at TURN_SPEED
BACKUP_MS = 300                 # how long to reverse when backing up
OBSTACLE_WAIT_MS = 2000         # how long to wait for another bot to move before turning away
HOME_TURN_DIR = "R"             # which way to spin while looking for our beacon
HOME_SEARCH_MS = 8000           # give up spinning after this long, nudge forward, and retry

##HELPERS##
def turn(direction, degrees):
    """Spin in place by roughly `degrees` (uses DEG_PER_SEC)."""
    driver.movement(direction, TURN_SPEED)
    sleep_ms(int(degrees / DEG_PER_SEC * 1000))
    driver.movement("S")

def back_up(ms=BACKUP_MS):
    driver.movement("B", DRIVE_SPEED)
    sleep_ms(ms)
    driver.movement("S")

def obstacle_ahead():
    """Checks for another bot in front. If one is there: stop, wait for it to move,
    and if it doesn't, turn away. Returns True if it had to deal with something."""
    front, back = ps.blocked()
    if not front:
        return False
    driver.movement("S")
    print("Obstacle! Waiting...")
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < OBSTACLE_WAIT_MS:
        sleep_ms(ps.PING_GAP_MS)
        if not ps.confirmed()[0]:
            print("Path cleared")
            return True                 # it moved; caller just carries on
    direction, angle = ps.random_turn()
    print("Still blocked, turning", direction, angle)
    turn(direction, angle)
    return True

##STATES##
SEARCH, PICKUP, HOME = "SEARCH", "PICKUP", "HOME"
state = SEARCH
home_spin_start = None

try:
    while True:
        # ---------- Safety: other bots, checked in every state ----------
        if obstacle_ahead():
            continue

        # ---------- SEARCH: drive forward, bounce off tape, watch for our color ----------
        if state == SEARCH:
            driver.movement("F", DRIVE_SPEED)

            left, right = rs.tape_sides()
            if left or right:
                print("Tape!")
                driver.movement("S")
                back_up()
                direction, angle = ps.random_turn(120, 240)   # roughly "turn around"
                turn(direction, angle)
                continue

            if cs.classify() == Team.get_color():
                print("Found our color!")
                driver.movement("S")
                state = PICKUP

        # ---------- PICKUP: back up, magnet on, grab, return to search position ----------
        elif state == PICKUP:
            back_up()
            electromagnet.value(1)
            servo.set_angle(grab_mode)
            sleep_ms(500)                       # let the arm reach the washer
            servo.set_angle(search_mode)
            sleep_ms(500)
            print("Picked up, homing to bin")
            home_spin_start = None
            state = HOME

        # ---------- HOME: spin until we see our beacon, drive at it, repeat ----------
        elif state == HOME:
            if ir.sees_team():
                home_spin_start = None
                driver.movement("F", DRIVE_SPEED)   # beacon in view: drive toward it
            else:
                if home_spin_start is None:
                    home_spin_start = ticks_ms()
                    print("Looking for beacon...")
                driver.movement(HOME_TURN_DIR, TURN_SPEED)
                if ticks_diff(ticks_ms(), home_spin_start) > HOME_SEARCH_MS:
                    print("Beacon not found; repositioning")
                    driver.movement("F", DRIVE_SPEED)
                    sleep_ms(500)
                    home_spin_start = None
            # TODO: detect arrival at the bin (e.g. front ultrasonic close while
            # sees_team()), then deposit with bin_deposit_mode_initial/final.

        sleep_ms(20)

finally:
    driver.stop()
    electromagnet.value(0)
    LED.value(0)