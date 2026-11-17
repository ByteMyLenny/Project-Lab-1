# ColorSensor.py
from machine import Pin, time_pulse_us
import time
import Sampling

# Pins: avoid GP0–3 and GP12–16 (motors and OCP)
S2 = Pin(5, Pin.OUT)
S3 = Pin(6, Pin.OUT)
OUT = Pin(7, Pin.IN)
# S0 → GND and S1 → 3.3 V for 2% scaling

FILTERS = {"red": (0, 0), "green": (1, 1), "blue": (0, 1), "clear": (1, 0)}

WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}   # loaded from the file, or set by calibrate_white()

# Every taught sample, grouped by name:
# {"FLOOR": [[r, g, b, bright], ...], "CYAN": [...], ...}
SAMPLES = {}

MAX_DISTANCE = 0.15       # a sample farther than this doesn't get a vote
BRIGHTNESS_WEIGHT = 0.5   # how much brightness counts vs. color
K = 5                     # how many nearest samples vote in classify()

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
    """Hold something white under the sensor, then run this.
    NOTE: changing white changes every reading, so old samples may no longer match."""
    for name in ("red", "green", "blue"):
        WHITE[name] = read_filter(name, cycles=30)
    print("WHITE =", WHITE)

# ---------- Fingerprints ----------
def features():
    """[red share, green share, blue share, brightness] for one reading."""
    r, g, b = read_rgb()
    total = r + g + b
    if total == 0:
        return [0.0, 0.0, 0.0, 0.0]
    return [r / total, g / total, b / total, total / 3]

def sample(n=5):
    """Average fingerprint over n readings."""
    acc = [0.0, 0.0, 0.0, 0.0]
    for _ in range(n):
        f = features()
        for i in range(4):
            acc[i] += f[i]
    return [round(a / n, 3) for a in acc]

# ---------- Saving / loading (through Sampling.py) ----------
def load_samples():
    """Load white calibration and all samples from the file on the Pico."""
    global SAMPLES
    data = Sampling.load()
    WHITE.update(data.get("white", {}))
    SAMPLES = data.get("samples", {})
    print("Loaded:", counts())

def save_samples():
    """Write white calibration and all samples to the file on the Pico."""
    Sampling.save({"white": WHITE, "samples": SAMPLES})
    print("Saved:", counts())

def teach(name, n=10, save=False):
    """Add a sample of whatever is under the sensor to `name`.
    Call several times per name for a bigger sample pool. save=True writes the file right away."""
    name = name.upper()
    s = sample(n)
    SAMPLES.setdefault(name, []).append(s)
    print("%s #%d: %s" % (name, len(SAMPLES[name]), s))
    if save:
        save_samples()

def undo(name):
    """Remove the most recent sample for `name` (e.g. a bad reading)."""
    name = name.upper()
    if SAMPLES.get(name):
        SAMPLES[name].pop()
        print("Removed last", name, "sample")

def forget(name):
    """Delete ALL samples for `name`."""
    SAMPLES.pop(name.upper(), None)
    print("Forgot", name.upper())

def counts():
    """How many samples each name has, e.g. {"FLOOR": 12, "CYAN": 8}."""
    return {name: len(lst) for name, lst in SAMPLES.items()}

# ---------- Classifying ----------
def distance(a, b):
    d = 0
    for i in range(3):
        d += (a[i] - b[i]) ** 2
    d += (BRIGHTNESS_WEIGHT * (a[3] - b[3])) ** 2
    return d ** 0.5

def classify(k=K):
    """The K closest samples vote. Returns the winning name, or "UNKNOWN"."""
    if not SAMPLES:
        return "NO SAMPLES (run teach mode)"
    f = sample(3)
    near = []
    for name, lst in SAMPLES.items():
        for s in lst:
            d = distance(f, s)
            if d <= MAX_DISTANCE:
                near.append((d, name))
    if not near:
        return "UNKNOWN"
    near.sort()
    votes = {}
    for d, name in near[:k]:
        votes[name] = votes.get(name, 0) + 1
    return max(votes, key=lambda n: votes[n])

# Load saved samples automatically when this module is imported
load_samples()

# ---------- Teach mode: run this file directly ----------
if __name__ == "__main__":
    if input("Recalibrate white? (y/N): ").strip().lower() == "y":
        if SAMPLES:
            print("Warning: existing samples were taken with the old white calibration.")
        input("Hold something WHITE under the sensor, then press Enter...")
        calibrate_white()

    print("\nTeach mode: hold something under the sensor, type its name, press Enter.")
    print("Names: FLOOR, CYAN, MAGENTA, YELLOW, NONE. Repeat a name to add more samples.")
    print("UNDO <name> removes the last sample | COUNTS | SAVE | GO = save and finish\n")
    while True:
        cmd = input("> ").strip().upper()
        if cmd == "GO":
            save_samples()
            break
        elif cmd == "SAVE":
            save_samples()
        elif cmd == "COUNTS":
            print(counts())
        elif cmd.startswith("UNDO "):
            undo(cmd[5:])
        elif cmd:
            teach(cmd)

    print("\nLive test:")
    while True:
        print(classify())
        time.sleep(0.5)