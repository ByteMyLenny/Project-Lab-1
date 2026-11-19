# ReflectanceDebug.py: sample floor + tape, then show live tape detection
import Reflectance_Sensor as rs, Servo as servo
from utime import sleep_ms

SEARCH_ANGLE = 160;

def read_avg(n=5):
    """Average of n full readings (all 8 sensors)."""
    acc = [0] * 8
    for _ in range(n):
        vals = rs.read_all()
        for i in range(8):
            acc[i] += vals[i]
    return [a // n for a in acc]

def sample_mode():
    floor_samples = []
    tape_samples = []
    print("Current thresholds:", rs.THRESHOLDS)
    print("f = sample FLOOR | t = sample TAPE | go = calculate, save, and start live view")
    print("Tip: if the tape is narrower than the sensor bar, sample TAPE several times,")
    print("     sliding it so every sensor gets a turn over the tape.")
    while True:
        cmd = input("> ").strip().lower()
        if cmd == "f":
            v = read_avg()
            floor_samples.append(v)
            print("FLOOR #%d:" % len(floor_samples), v)
        elif cmd == "t":
            v = read_avg()
            tape_samples.append(v)
            print("TAPE  #%d:" % len(tape_samples), v)
        elif cmd == "go":
            if not floor_samples or not tape_samples:
                print("Need at least one FLOOR and one TAPE sample first.")
                continue
            calculate(floor_samples, tape_samples)
            return

def calculate(floor_samples, tape_samples):
    # Floor: average per sensor
    floor = [sum(s[i] for s in floor_samples) // len(floor_samples) for i in range(8)]
    # Tape: per sensor, the sample farthest from the floor (that's when the tape was under it)
    tape = []
    for i in range(8):
        tape.append(max((s[i] for s in tape_samples), key=lambda v: abs(v - floor[i])))

    lower = sum(1 for i in range(8) if tape[i] < floor[i])
    rs.TAPE_VALUE_IS_LOWER_THAN_FLOOR = lower >= 4
    rs.THRESHOLDS = [(floor[i] + tape[i]) // 2 for i in range(8)]

    print("\nFloor:     ", floor)
    print("Tape:      ", tape)
    print("Thresholds:", rs.THRESHOLDS)
    print("Tape reads", "LOWER" if rs.TAPE_VALUE_IS_LOWER_THAN_FLOOR else "HIGHER", "than floor")
    weak = [i for i in range(8) if abs(floor[i] - tape[i]) < rs.MIN_CONTRAST]
    if weak:
        print("WARNING: weak floor/tape difference on sensors", weak,
              "- the tape may not have been under them, or the height is off")
    rs.save_thresholds()

def live_view():
    print("\nLive view (Ctrl+C to stop).  T = tape, . = floor   sensors 0..7 (left to right)")
    while True:
        vals = rs.read_all()
        hits = [rs.is_tape(v, i) for i, v in enumerate(vals)]
        bar = " ".join("T" if h else "." for h in hits)
        left, right = any(hits[:4]), any(hits[4:])
        if left and right:
            status = "TAPE (both sides)"
        elif left:
            status = "TAPE LEFT"
        elif right:
            status = "TAPE RIGHT"
        else:
            status = "floor"
        print("[%s]  %-17s %s" % (bar, status, vals))
        sleep_ms(200)

if __name__ == "__main__":
    servo.set_angle(SEARCH_ANGLE)
    sample_mode()
    live_view()