# DEBUG_PROXSENSOR.py: 4-step wall routine using front AND back proximity sensors
import MotorDriver as driver, ProximitySensors as ps
from utime import sleep_ms

DRIVE_SPEED = driver.SPEED + 10       # forward / backward speed (%)
TURN_SPEED = driver.SPEED + 15     # spin-in-place speed (%); raise if turns stall
STOP_CM = 15                      # react when a wall is this close
BACKUP_MS = 400                   # how long to move away from a wall before turning
DEG_PER_SEC = 73.75               # measured spin rate at TURN_SPEED

ps.STOP_DISTANCE_CM = STOP_CM

def turn_around():
    driver.movement("R", TURN_SPEED)
    sleep_ms(int(180 / DEG_PER_SEC * 1000))
    driver.movement("S")
    sleep_ms(200)

def move_for(direction, ms):
    driver.movement(direction, DRIVE_SPEED)
    sleep_ms(ms)
    driver.movement("S")
    sleep_ms(200)

def drive_until_wall(direction):
    """Drive "F" or "B" until the sensors on that end see a wall, then stop."""
    side = 0 if direction == "F" else 1          # 0 = front sensors, 1 = back sensors
    name = "front" if side == 0 else "back"
    while True:
        driver.movement(direction, DRIVE_SPEED)
        dist = ps.ping()[side]
        print(name, ":", "-" if dist is None else "%.1f cm" % dist)
        if dist is not None and dist < STOP_CM:
            driver.movement("S")
            if ps.confirmed(2)[side]:            # double-check it's really a wall
                print("Wall on the", name)
                sleep_ms(200)
                return
        sleep_ms(ps.PING_GAP_MS)                 # sensors need ~60 ms between pings

try:
    while True:
        # 1. Forward to a wall, back up, turn around
        print("\nStep 1: forward, then back up and turn around")
        drive_until_wall("F")
        move_for("B", BACKUP_MS)
        turn_around()

        # 2. Forward to a wall, then switch straight to reverse
        print("\nStep 2: forward, then reverse")
        drive_until_wall("F")

        # 3. Reverse to a wall, pull away, turn around, keep reversing
        print("\nStep 3: backward, then turn around")
        drive_until_wall("B")
        move_for("F", BACKUP_MS)
        turn_around()

        # 4. Reverse to a wall, then switch to forward
        print("\nStep 4: backward, then forward")
        drive_until_wall("B")
finally:
    driver.stop()