# TapeBounce.py
# Drive forward until any reflectance sensor sees tape,
# back up a little, turn around, and repeat forever.
# Ctrl+C stops the motors.

from utime import sleep, sleep_ms
import MotorDriver as driver
import Reflectance_Sensor as rs

# ---- Settings ----
DRIVE_SPEED = driver.SPEED + 10         # forward speed
TURN_SPEED = driver.SPEED + 5       # same turn speed main.py uses
DEG_PER_SEC = 73.75                 # measured at TURN_SPEED
BACKUP_MS = 300                     # back off the tape before turning
TAPE_HITS = 2                       # readings in a row needed to count as tape


def sees_tape():
    # True if any of the 8 sensors is on tape
    values = rs.read_all()
    for ch in range(8):
        if rs.is_tape(values[ch], ch):
            return True
    return False


def turn_around():
    driver.movement("S")
    sleep_ms(150)

    # back up so the sensor gets off the tape
    driver.movement("B", DRIVE_SPEED)
    sleep_ms(BACKUP_MS)
    driver.movement("S")
    sleep_ms(150)

    # spin 180 degrees
    driver.movement("R", TURN_SPEED)
    sleep(180 / DEG_PER_SEC)
    driver.movement("S")
    sleep_ms(150)


def run():
    print("Thresholds:", rs.THRESHOLDS)
    print("Starting in 3 s... Ctrl+C to stop")
    sleep(3)

    hits = 0
    try:
        while True:
            driver.movement("F", DRIVE_SPEED)

            if sees_tape():
                hits += 1
            else:
                hits = 0

            if hits >= TAPE_HITS:
                print("TAPE -> turning around")
                turn_around()
                hits = 0

            sleep_ms(5)
    except KeyboardInterrupt:
        pass
    finally:
        driver.movement("S")
        print("Stopped")


run()