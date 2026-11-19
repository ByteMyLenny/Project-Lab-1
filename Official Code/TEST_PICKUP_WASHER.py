# WasherTest.py
# 1. Asks which team you are.
# 2. Drives forward until the color sensor sees your team's washer,
#    then backs up slowly, drops the arm with the magnet on,
#    lifts back to the search angle, and stops.
# 3. If something is too close in front, or it sees tape:
#    backs up, turns around, and stops.
# Ctrl+C stops the motors.

from machine import Pin
from utime import sleep, sleep_ms
import MotorDriver as driver
import ColorSensor as cs
import ProximitySensors as prox
import Reflectance_Sensor as rs
import Servo as servo

# ---- Settings ----
SEARCH_ANGLE = 160
GRAB_ANGLE = 180

DRIVE_SPEED = driver.SPEED -5
SLOW_SPEED = driver.SPEED - 5       # slow back-up for the pickup
TURN_SPEED = driver.SPEED + 5
DEG_PER_SEC = 73.75                 # measured at TURN_SPEED

PICKUP_BACKUP_MS = 200              # how long to back up slowly before grabbing
ESCAPE_BACKUP_MS = 500              # how long to back up before turning around
STOP_CM = 15                        # "too close" distance
HITS_NEEDED = 2                     # readings in a row before acting

magnet = Pin(28, Pin.OUT)
magnet.value(0)


# ---------- Team ----------
def ask_team():
    while True:
        choice = input("Team? (M = MAGENTA, Y = YELLOW, C = CYAN): ").strip().upper()
        if choice == "M":
            return "MAGENTA"
        if choice == "Y":
            return "YELLOW"
        if choice == "C":
            return "CYAN"
        print("Type M, Y, or C")


# ---------- Sensor checks ----------
def sees_tape():
    values = rs.read_all()
    for ch in range(8):
        if rs.is_tape(values[ch], ch):
            return True
    return False


def too_close():
    reading = prox.ping()
    if reading is None:
        return False
    front = reading[0]
    return front is not None and front < STOP_CM


def sees_washer(team):
    return cs.classify() == team


# ---------- Actions ----------
def turn_around_and_stop(reason):
    print(reason, "-> backing up, turning around, stopping")
    driver.movement("S")
    sleep_ms(150)
    driver.movement("B", DRIVE_SPEED)
    sleep_ms(ESCAPE_BACKUP_MS)
    driver.movement("S")
    sleep_ms(150)
    driver.movement("R", TURN_SPEED)
    sleep(180 / DEG_PER_SEC)
    driver.movement("S")


def pick_up():
    print("WASHER -> picking up")
    driver.movement("S")
    sleep_ms(150)

    # back up slowly so the magnet lands on the washer
    driver.movement("B", SLOW_SPEED)
    sleep_ms(PICKUP_BACKUP_MS)
    driver.movement("S")
    sleep_ms(150)

    # magnet on, drop the arm, lift back up
    magnet.value(1)
    servo.set_angle(GRAB_ANGLE)
    sleep(1)
    servo.set_angle(SEARCH_ANGLE)
    sleep(1)
    print("Done. Magnet still ON (holding the washer)")

def check_washer(team):
    """Stop, then read the color while sitting still. Nudge back once if needed."""
    driver.movement("S")
    sleep_ms(200)
    for attempt in range(2):
        votes = [cs.classify() for _ in range(3)]
        print("  still check:", votes)
        if votes.count(team) >= 2:
            return True
        # might have rolled past it, back up a tiny bit and try once more
        driver.movement("B", SLOW_SPEED)
        sleep_ms(120)
        driver.movement("S")
        sleep_ms(200)
    return False
# ---------- Main ----------
def run():
    servo.set_angle(SEARCH_ANGLE)
    team = ask_team()
    print("Team:", team)

    servo.set_angle(SEARCH_ANGLE)
    print("Starting in 3 s... Ctrl+C to stop")
    sleep(3)

    washer_hits = 0
    tape_hits = 0
    close_hits = 0

    try:
            while True:
                from utime import ticks_ms, ticks_diff
                t0 = ticks_ms()
                color = cs.classify()
                t1 = ticks_ms()
                values = rs.read_all()
                t2 = ticks_ms()
                reading = prox.ping()
                t3 = ticks_ms()
                print("ms  color:", ticks_diff(t1, t0), "tape:", ticks_diff(t2, t1), "prox:", ticks_diff(t3, t2))
                driver.movement("F", DRIVE_SPEED)

                

                print("COLOR:", color, "| TAPE VALS:", values, "| PROX:", reading)

                washer_hits = washer_hits + 1 if color == team else 0

                tape = False
                for ch in range(8):
                    if rs.is_tape(values[ch], ch):
                        tape = True
                tape_hits = tape_hits + 1 if tape else 0

                close = reading is not None and reading[0] is not None and reading[0] < STOP_CM
                close_hits = close_hits + 1 if close else 0

                if washer_hits >= HITS_NEEDED:
                    pick_up()
                    break
                if close_hits >= HITS_NEEDED:
                    turn_around_and_stop("TOO CLOSE")
                    break
                if tape_hits >= HITS_NEEDED:
                    turn_around_and_stop("TAPE")
                    break
    except KeyboardInterrupt:
        magnet.value(0)
    finally:
        driver.movement("S")
        print("Stopped")


run()