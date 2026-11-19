# Setup.py
# Pre-round setup: IR remote team selection, start trigger, and calibration helpers.
# The kit remote sends NEC codes (not the beacon's UART text), so this decodes NEC itself.
from machine import Pin, time_pulse_us
from utime import sleep_ms, ticks_ms, ticks_diff
import rp2
import Team
import Sampling

IR_PIN = 10                       # TSOP38238 OUT (GP10 = physical pin 14)
SETTINGS_FILE = "settings.json"

# Remote button codes. These are common for the Elegoo/kit remotes, but VERIFY
# yours with learn_buttons() and fix any that don't match.
TEAM_BUTTONS = {0x0C: "MAGENTA",  # button 1
                0x18: "YELLOW",   # button 2
                0x5E: "CYAN"}     # button 3
START_BUTTONS = (0x40, 0x43)      # play/pause or OK, depending on the remote
REMOTE_ADDRESS = 0x00             # Elegoo remote; the beacons use 0x55

_led = Pin("LED", Pin.OUT, value=0)
_ir = None

def _pin():
    global _ir
    if _ir is None:
        _ir = Pin(IR_PIN, Pin.IN, Pin.PULL_UP)
    return _ir

# ---------- NEC remote decoding ----------
from array import array
from utime import ticks_us
import micropython
micropython.alloc_emergency_exception_buf(100)

_MAX_EDGES = 100
_times = array("i", [0] * _MAX_EDGES)    # time of each edge, µs after the first
_n = 0
_t0 = 0
_first_low = True

def _edge(pin):
    """Interrupt: record the time of every rising/falling edge."""
    global _n, _t0, _first_low
    t = ticks_us()
    if _n == 0:
        _t0 = t
        _first_low = pin.value() == 0
    if _n < _MAX_EDGES:
        _times[_n] = ticks_diff(t, _t0)
        _n += 1

def _decode(n):
    """Turn recorded edges into an NEC command byte, "REPEAT", or None."""
    d = [_times[i + 1] - _times[i] for i in range(n - 1)]   # pulse lengths
    start = 0 if _first_low else 1                         # which entries are LOW pulses
    for k in range(start, len(d) - 1, 2):
        if 8000 < d[k] < 10000:                            # 9 ms leading pulse
            gap = d[k + 1]
            if 2000 < gap < 2700:
                return "REPEAT"                            # button being held
            if not 4000 < gap < 5000:
                return None
            bits = d[k + 2:]
            if len(bits) < 64:
                return None
            b = [0, 0, 0, 0]
            for i in range(32):
                if bits[2 * i + 1] > 1000:                 # long gap = 1
                    b[i // 8] |= 1 << (i % 8)
            if b[2] ^ b[3] != 0xFF:                        # built-in error check
                return None
            if b[0] != REMOTE_ADDRESS:                     # ignore beacons and other remotes
                return None
            return b[2]
    return None

def read_button(timeout_ms=100):
    """Waits up to timeout_ms for one remote button press.
    Returns the button code (0-255), "REPEAT" if a button is being held, or None."""
    global _n
    pin = _pin()
    _n = 0
    pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=_edge)
    # type: ignore
    start = ticks_ms()
    while _n == 0:
        if ticks_diff(ticks_ms(), start) > timeout_ms:
            pin.irq(handler=None)
            return None
    sleep_ms(80)                                           # a full NEC frame is ~68 ms
    pin.irq(handler=None)
    return _decode(_n)

def learn_buttons():
    """Press remote buttons; prints each code. Use it to fill in TEAM_BUTTONS / START_BUTTONS.
    Ctrl+C to stop."""
    print("Press buttons on the remote (Ctrl+C to stop)...")
    while True:
        code = read_button(200)
        if isinstance(code, int):
            print("button code: 0x%02X" % code)

# ---------- LED feedback ----------
def blink(times, on_ms=200, off_ms=200):
    for _ in range(times):
        _led.value(1)
        sleep_ms(on_ms)
        _led.value(0)
        sleep_ms(off_ms)

# ---------- Beacon calibration (calibration day) ----------
BEACON_FILE = "beacon_codes.json"

def learn_beacon(color, scan_ms=3000):
    """Point the receiver at ONE beacon and run this. Saves that beacon's code under `color`."""
    import IR_Receiver as irr
    color = color.upper()
    if color not in Team.COLORS:
        print("Unknown color:", color)
        return None
    print("Scanning for", color, "beacon...")
    ir = irr.IRReceiver(pin=IR_PIN)
    code = ir.scan(scan_ms)
    ir.stop()
    if code is None:
        print("No beacon signal found. Check it's on and aimed into the receiver's slot.")
        blink(1, on_ms=1000)                          # one long blink = failed
        return None
    codes = Sampling.load(BEACON_FILE, default={})
    for other, c in codes.items():
        if c == code and other != color:
            print("WARNING: this code was already saved as", other)
    codes[color] = code
    Sampling.save(codes, BEACON_FILE)
    print("Saved %s = 0x%04X" % (color, code))
    blink(Team.COLORS.index(color) + 1)
    return code

def calibrate_beacons():
    """Remote-driven: press 1/2/3 for the color the TA says, while aimed at that beacon.
    Press POWER (0x45) when done."""
    print("Beacon calibration: aim at a beacon, press 1 = MAGENTA, 2 = YELLOW, 3 = CYAN.")
    print("Press POWER on the remote when finished.")
    while True:
        _led.toggle()
        code = read_button(250)
        if code == 0x45:
            break
        if code in TEAM_BUTTONS:
            _led.value(0)
            sleep_ms(500)                             # time to aim back at the beacon
            learn_beacon(TEAM_BUTTONS[code])
    _led.value(0)
    show_beacons()

def show_beacons():
    """Prints every saved beacon code."""
    codes = Sampling.load(BEACON_FILE, default={})
    if not codes:
        print("No beacons calibrated yet.")
    for color in Team.COLORS:
        code = codes.get(color)
        print("%-8s %s" % (color, "0x%04X" % code if code is not None else "not set"))

# ---------- Team selection ----------
def load_saved_team():
    """Restore the last selected team from the Pico (if any). Returns it or None."""
    color = Sampling.load(SETTINGS_FILE, default={}).get("team")
    if color in Team.COLORS:
        Team.set_color(color)
        return color
    return None

def select_team(timeout_s=None):
    """Waits for button 1/2/3 on the remote, sets the team, and blinks to confirm
    (1 blink = MAGENTA, 2 = YELLOW, 3 = CYAN). Saves the choice.
    timeout_s=None waits forever; otherwise falls back to the saved team.
    Returns the selected color."""
    print("Select team: 1 = MAGENTA, 2 = YELLOW, 3 = CYAN")
    start = ticks_ms()
    while timeout_s is None or ticks_diff(ticks_ms(), start) < timeout_s * 1000:
        _led.toggle()                               # slow flash = waiting
        code = read_button(250)
        if code in TEAM_BUTTONS:
            color = TEAM_BUTTONS[code]
            Team.set_color(color)
            Sampling.save({"team": color}, SETTINGS_FILE)
            _led.value(0)
            sleep_ms(300)
            blink(Team.COLORS.index(color) + 1)
            print("Team:", color)
            return color
    _led.value(0)
    color = load_saved_team()
    print("No selection; using saved team:", color)
    return color

# ---------- Start trigger ----------
def wait_for_start():
    """Waits for the START remote button or the Pico's BOOTSEL button.
    LED stays on while waiting, then turns off and the run begins."""
    print("Ready. Press START on the remote or the BOOTSEL button to begin.")
    _led.value(0)
    sleep_ms(2000)
    Team.blink_color()
    sleep_ms(1000)
    _led.value(1)
    while True:
        if rp2.bootsel_button():
            break
        if read_button(100) in START_BUTTONS:
            break
    _led.value(0)
    sleep_ms(300)                                   # time to pull your hand away
    print("GO")

# ---------- Calibration helpers (run during calibration time) ----------
def calibrate_tape():
    """Floor/tape calibration for the reflectance sensor; applies and saves it."""
    import Reflectance_Sensor as rs
    rs.calibrate()

def check_colors(seconds=10):
    """Prints live color classifications so you can verify the saved samples in this room."""
    import ColorSensor as cs
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < seconds * 1000:
        print(cs.classify())
        sleep_ms(300)

# ---------- Everything right before a round ----------
def run(team_timeout_s=None):
    """Team selection, then wait for the start signal. Returns the team color."""
    color = select_team(team_timeout_s)
    wait_for_start()
    return color