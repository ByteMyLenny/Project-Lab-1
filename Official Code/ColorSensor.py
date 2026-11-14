# ColorSensor.py
from machine import Pin, time_pulse_us
import time

# Pins are placeholders; avoid GP0–3 and GP12–16 (motors and OCP)
S2 = Pin(5, Pin.OUT)
S3 = Pin(6, Pin.OUT)
OUT = Pin(7, Pin.IN)
# S0 → GND and S1 → 3.3 V for 2% scaling

FILTERS = {"red": (0, 0), "green": (1, 1), "blue": (0, 1), "clear": (1, 0)}

WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}   # set with calibrate_white()

# Fingerprints: name → (red share, green share, blue share, brightness)
# Fill these in with teach mode (run this file directly), then paste them here.
REFERENCES = {
}

MAX_DISTANCE = 0.15       # farther than this from every reference = "UNKNOWN"
BRIGHTNESS_WEIGHT = 0.5   # how much brightness counts vs. color

# ---------- Reading ----------
def read_filter(name, cycles=10):
    """Average frequency (Hz) through one filter."""
    S2.value(FILTERS[name][0])
    S3.value(FILTERS[name][1])
    time.sleep_ms(20)
    total = 0
    good = 0
    for _ in range(cycles):
        high = time_pulse_us(OUT, 1, 100000)
        low = time_pulse_us(OUT, 0, 100000)
        if high > 0 and low > 0:          # skip timeouts
            total += high + low
            good += 1
    if good == 0:
        return 0
    return 1_000_000 / (total / good)

def read_rgb():
    """Red, green, and blue, each scaled so white reads about 1.0."""
    return (read_filter("red") / WHITE["red"],
            read_filter("green") / WHITE["green"],
            read_filter("blue") / WHITE["blue"])

def calibrate_white():
    """Hold something white under the sensor, then run this."""
    for name in ("red", "green", "blue"):
        WHITE[name] = read_filter(name, cycles=30)
    print("WHITE =", WHITE)

# ---------- Fingerprints ----------
def features():
    """(red share, green share, blue share, brightness) for one reading."""
    r, g, b = read_rgb()
    total = r + g + b
    if total == 0:
        return (0, 0, 0, 0)
    return (r / total, g / total, b / total, total / 3)

def sample(n=5):
    """Average fingerprint over n readings."""
    acc = [0.0, 0.0, 0.0, 0.0]
    for _ in range(n):
        f = features()
        for i in range(4):
            acc[i] += f[i]
    return tuple(round(a / n, 3) for a in acc)

def teach(name, n=10):
    """Save a fingerprint for whatever is under the sensor right now."""
    REFERENCES[name] = sample(n)
    print('    "%s": %s,' % (name, REFERENCES[name]))

def distance(a, b):
    d = 0
    for i in range(3):
        d += (a[i] - b[i]) ** 2
    d += (BRIGHTNESS_WEIGHT * (a[3] - b[3])) ** 2
    return d ** 0.5

def classify():
    """Returns the closest saved name (e.g. "CYAN", "FLOOR"), or "UNKNOWN"."""
    if not REFERENCES:
        return "NO REFERENCES (run teach mode)"
    f = sample(3)
    best, best_d = "UNKNOWN", 1e9
    for name, ref in REFERENCES.items():
        d = distance(f, ref)
        if d < best_d:
            best, best_d = name, d
    if best_d > MAX_DISTANCE:
        return "UNKNOWN"
    return best.split("_")[0]     # "CYAN_2" counts as "CYAN"

# ---------- Teach mode: run this file directly ----------
if __name__ == "__main__":
    input("Hold something WHITE under the sensor, then press Enter...")
    calibrate_white()

    print("\nTeach mode: hold an object under the sensor, type its name, press Enter.")
    print("Suggested: FLOOR, CYAN, MAGENTA, YELLOW, NONE (nothing under it).")
    print("Extra samples: add _2, _3 (e.g. CYAN_2). Type GO when done.\n")
    while True:
        name = input("Name (or GO): ").strip().upper()
        if name == "GO":
            break
        if name:
            teach(name)

    print("\nPaste these into the file:")
    print("WHITE =", WHITE)
    print("REFERENCES = {")
    for k, v in REFERENCES.items():
        print('    "%s": %s,' % (k, v))
    print("}")

    print("\nLive test:")
    while True:
        print(classify())
        time.sleep(0.5)