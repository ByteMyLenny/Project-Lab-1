# BeaconSpinTest.py
# 1. Press 1 / 2 / 3 on the remote to pick the team.
# 2. The robot spins in place until the IR receiver sees that team's beacon,
#    then stops.
# Ctrl+C stops the motors.
#
# Remote buttons: 1 = MAGENTA, 2 = YELLOW, 3 = CYAN

from machine import Pin
from utime import ticks_us, ticks_ms, ticks_diff, sleep_ms
import array
import MotorDriver as driver

# ---- Settings ----
IR_PIN = 10
SPIN_SPEED = driver.SPEED + 5     # slow it down if it spins past the beacon

LISTEN_MS = 200                   # how long each listen window is (an NEC frame is ~68 ms)
HITS_NEEDED = 2                   # matching frames before it counts as found

REMOTE_ADDRESS = 0x00
TEAM_BUTTONS = {0x0C: "MAGENTA", 0x18: "YELLOW", 0x5E: "CYAN"}

BEACON_ADDRESS = 0x55
BEACON_CODES = {"YELLOW": 0xC5, "CYAN": 0x00, "MAGENTA": 0x3F}

# ---------- NEC decoder ----------
MAX_EDGES = 200
times = array.array("i", [0] * MAX_EDGES)
count = array.array("i", [0])

def _edge(pin):
    i = count[0]
    if i < MAX_EDGES:
        times[i] = ticks_us()
        count[0] = i + 1

ir = Pin(IR_PIN, Pin.IN, Pin.PULL_UP)
ir.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=_edge, hard=True)  # type: ignore


def _near(value, target, tol):
    return abs(value - target) <= tol


def _decode(n):
    """Look through the captured edges for full NEC frames.
    Returns a list of (address, command)."""
    frames = []
    i = 0
    while i + 67 < n:
        lead_low = ticks_diff(times[i + 1], times[i])
        lead_high = ticks_diff(times[i + 2], times[i + 1])
        if _near(lead_low, 9000, 1500) and _near(lead_high, 4500, 1000):
            data = [0, 0, 0, 0]
            ok = True
            for bit in range(32):
                k = i + 2 + 2 * bit
                high = ticks_diff(times[k + 2], times[k + 1])
                if high > 1000:
                    data[bit // 8] |= 1 << (bit % 8)
                elif high < 300:
                    ok = False
                    break
            if ok and (data[2] ^ data[3]) == 0xFF:
                frames.append((data[0], data[2]))
            i += 66
        else:
            i += 1
    return frames


def listen(ms=LISTEN_MS):
    """Capture IR for `ms` milliseconds and return any frames decoded."""
    count[0] = 0
    sleep_ms(ms)
    return _decode(count[0])


# ---------- Team select ----------
def pick_team():
    print("Press 1 = MAGENTA, 2 = YELLOW, 3 = CYAN on the remote")
    while True:
        for addr, cmd in listen(300):
            if addr == REMOTE_ADDRESS and cmd in TEAM_BUTTONS:
                return TEAM_BUTTONS[cmd]


# ---------- Main ----------
def run():
    team = pick_team()
    code = BEACON_CODES[team]
    print("Team:", team, "| looking for address 0x%02X command 0x%02X" % (BEACON_ADDRESS, code))
    sleep_ms(1000)

    hits = 0
    try:
        driver.movement("R", SPIN_SPEED)
        while True:
            frames = listen()
            for addr, cmd in frames:
                print("  saw 0x%02X 0x%02X" % (addr, cmd))
            if (BEACON_ADDRESS, code) in frames:
                hits += 1
            else:
                hits = 0
            if hits >= HITS_NEEDED:
                driver.movement("S")
                print("FOUND", team, "beacon!")
                break
    except KeyboardInterrupt:
        pass
    finally:
        driver.movement("S")
        print("Stopped")


run()