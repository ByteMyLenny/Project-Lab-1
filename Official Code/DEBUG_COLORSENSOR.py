# DEBUG_COLORSENSOR.py: For Basic Testing/Debugging. A playground.
import MotorDriver as driver, ColorSensor as cs, Servo as servo, Reflectance_Sensor as rs
from machine import Pin
from utime import sleep_ms, ticks_ms, ticks_diff

SEARCH_ANGLE = 160;

def classify_reading(f):
    """Same vote as cs.classify(), but on a reading we already took."""
    near = []
    for name, lst in cs.SAMPLES.items():
        for s in lst:
            d = cs.distance(f, s)
            if d <= cs.MAX_DISTANCE:
                near.append((d, name))
    if not near:
        return "UNKNOWN", None
    near.sort()
    votes = {}
    for d, name in near[:cs.K]:
        votes[name] = votes.get(name, 0) + 1
    return max(votes, key=lambda n: votes[n]), near[0][0]

def teach_mode():
    print("Current samples:", cs.counts())
    print("Type a NAME to sample it (FLOOR, MAGENTA, YELLOW, CYAN, NONE...)")
    print("white = recalibrate white | u = undo last | c = counts | go = save and start live view")
    last = None
    while True:
        cmd = input("> ").strip().upper()
        if not cmd:
            continue
        if cmd == "GO":
            cs.save_samples()
            return
        elif cmd == "WHITE":
            input("Hold something WHITE under the sensor, then press Enter...")
            cs.calibrate_white()
        elif cmd == "U":
            if last:
                cs.undo(last)
        elif cmd == "C":
            print(cs.counts())
        else:
            cs.teach(cmd)
            last = cmd

def live_view():
    print("\nLive view (Ctrl+C to stop)")
    print("%-9s %6s %6s %6s %7s | %5s %5s %5s | %s" %
          ("RESULT", "R", "G", "B", "BRIGHT", "r%", "g%", "b%", "closest"))
    while True:
        r, g, b = cs.read_rgb()
        total = r + g + b
        if total == 0:
            print("No signal (check sensor wiring: OE to GND, S0/S1, power)")
            sleep_ms(500)
            continue
        f = [r / total, g / total, b / total, total / 3]
        name, dist = classify_reading(f)
        print("%-9s %6.2f %6.2f %6.2f %7.2f | %5.3f %5.3f %5.3f | %s" %
              (name, r, g, b, f[3], f[0], f[1], f[2],
               "%.3f" % dist if dist is not None else "-"))
        sleep_ms(300)

if __name__ == "__main__":
    servo.set_angle(SEARCH_ANGLE)
    teach_mode()
    live_view()