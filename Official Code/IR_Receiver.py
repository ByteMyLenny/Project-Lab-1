# IR_Receiver.py
# Beacons send NEC codes. Which code means which color is learned on calibration day
# (Setup.calibrate_beacons) and saved in beacon_codes.json.
from machine import Pin
from utime import ticks_us, ticks_ms, ticks_diff, sleep_ms
from array import array
import micropython
import Team, Sampling

micropython.alloc_emergency_exception_buf(100)

BEACON_FILE = "beacon_codes.json"
REMOTE_ADDRESS = 0x00      # frames with this address are the Elegoo remote, not a beacon
BUF = 64                   # ring buffer size (power of 2)

def load_codes():
    """{"MAGENTA": code, ...} as saved by Setup.calibrate_beacons()."""
    return Sampling.load(BEACON_FILE, default={})

class IRReceiver:
    def __init__(self, pin=10, timeout_ms=600):
        """
        pin:        TSOP38238 OUT pin (GP10 = physical pin 14).
        timeout_ms: how long a beacon still counts as "seen" after its last frame.
        """
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.timeout_ms = timeout_ms
        self.reload_codes()

        # Decoder state (updated inside the interrupt; no memory allocation allowed there)
        self._last_us = ticks_us()
        self._state = 0                 # 0 = idle, 1 = got 9 ms lead, 2 = reading bits
        self._bits = 0
        self._b = bytearray(4)
        self._ring = array("H", [0] * BUF)
        self._head = 0
        self._tail = 0
        self._last_edge_ms = None

        self._last_code = None
        self._last_frame_ms = None
        self.last_seen = {}             # color -> time last seen
        self.last_color = None

        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING,
                     handler=self._edge, hard=True)

    def stop(self):
        self.pin.irq(handler=None)

    def reload_codes(self):
        """Re-read beacon_codes.json (e.g. after calibrating)."""
        self.codes = load_codes()
        self.code_to_color = {code: color for color, code in self.codes.items()}

    # ---------- Interrupt: decode NEC frames as the edges arrive ----------
    def _edge(self, p):
        t = ticks_us()
        d = ticks_diff(t, self._last_us)
        self._last_us = t
        self._last_edge_ms = ticks_ms()
        if p.value():                   # the pulse that just ended was LOW
            if 8000 < d < 10000:
                self._state = 1
            elif self._state == 2 and not (300 < d < 900):
                self._state = 0
        else:                           # the pulse that just ended was HIGH
            if self._state == 1:
                if 4000 < d < 5000:
                    self._state = 2
                    self._bits = 0
                    b = self._b
                    b[0] = 0; b[1] = 0; b[2] = 0; b[3] = 0
                else:
                    self._state = 0     # repeat code or junk
            elif self._state == 2:
                if 300 < d < 2000:
                    if d > 1000:
                        self._b[self._bits >> 3] |= 1 << (self._bits & 7)
                    self._bits += 1
                    if self._bits == 32:
                        b = self._b
                        if (b[2] ^ b[3]) == 0xFF and b[0] != REMOTE_ADDRESS:
                            h = self._head
                            self._ring[h] = (b[0] << 8) | b[2]     # address + command
                            self._head = (h + 1) & (BUF - 1)
                        self._state = 0
                else:
                    self._state = 0

    # ---------- Main-code side ----------
    def update(self):
        now = ticks_ms()
        while self._tail != self._head:
            code = self._ring[self._tail]
            self._tail = (self._tail + 1) & (BUF - 1)
            self._last_code = code
            self._last_frame_ms = now
            color = self.code_to_color.get(code)
            if color:
                self.last_seen[color] = now
                self.last_color = color

    def _recent(self, t):
        return t is not None and ticks_diff(ticks_ms(), t) < self.timeout_ms

    def sees_ir(self):
        """True if any IR arrived recently (any 38 kHz source, decoded or not)."""
        return self._recent(self._last_edge_ms)

    def sees_signal(self):
        """True if any beacon frame was decoded recently (known color or not)."""
        self.update()
        return self._recent(self._last_frame_ms)

    def read_beacon(self):
        """Color of the beacon most recently seen ("MAGENTA"/"YELLOW"/"CYAN"), or None."""
        self.update()
        if self.last_color and self._recent(self.last_seen.get(self.last_color)):
            return self.last_color
        return None

    def sees(self, color):
        """True if that color's beacon was seen recently. Example: ir.sees("CYAN")"""
        self.update()
        return self._recent(self.last_seen.get(color.upper()))

    def sees_team(self):
        """True if YOUR team's beacon (set in Team.py) was seen recently."""
        color = Team.get_color()
        return color is not None and self.sees(color)

    def last_code(self):
        """Most recent beacon code as hex (address+command), or None. For debugging."""
        self.update()
        return None if self._last_code is None else "0x%04X" % self._last_code

    def scan(self, ms=3000, min_frames=3):
        """Listens for `ms` and returns the most common beacon code, or None."""
        self.update()
        counts = {}
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < ms:
            while self._tail != self._head:
                code = self._ring[self._tail]
                self._tail = (self._tail + 1) & (BUF - 1)
                counts[code] = counts.get(code, 0) + 1
            sleep_ms(20)
        if not counts:
            return None
        best = max(counts, key=lambda c: counts[c])
        return best if counts[best] >= min_frames else None