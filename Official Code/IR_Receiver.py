# IR_Receiver.py
# Reads the beacon messages from the project scope: 38 kHz IR carrying
# ASCII strings "MAGENTA", "YELLOW_", "CYAN___", decoded as serial (UART) data.
# Uses PIO so it works on any pin (GP10 here).

# pyright: reportUndefinedVariable=false, reportCallIssue=false, reportIndexIssue=false
import rp2
from machine import Pin
from utime import ticks_ms, ticks_diff, sleep_ms
import Team

MESSAGES = {b"MAGENTA": "MAGENTA", b"YELLOW_": "YELLOW", b"CYAN___": "CYAN"}

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_RIGHT)
def _uart_rx():
    label("start")
    wait(0, pin, 0)               # wait for the start bit (line goes LOW)
    set(x, 7)                 [10]  # move to the middle of the first data bit
    label("bitloop")
    in_(pins, 1)                  # read one bit
    jmp(x_dec, "bitloop")     [6]   # 8 bits total, 8 PIO cycles each
    jmp(pin, "good_stop")         # stop bit should be HIGH
    wait(1, pin, 0)               # bad frame: wait for idle, discard
    jmp("start")
    label("good_stop")
    push(noblock)


class IRReceiver:
    def __init__(self, pin=10, baud=1200, sm_id=0, timeout_ms=600):
        """
        pin:  TSOP38238 OUT pin (GP10 = physical pin 14).
        baud: beacon speed. Not in the project PDF; find it with find_baud().
        timeout_ms: how long a beacon still counts as "seen" after its last message.
        """
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.sm = rp2.StateMachine(sm_id, _uart_rx, freq=8 * baud,
                                   in_base=self.pin, jmp_pin=self.pin)
        self.sm.active(1)
        self.timeout_ms = timeout_ms
        self.buf = b""
        self.last_byte_ms = None
        self.last_seen = {}          # color -> time last decoded
        self.last_color = None

    def stop(self):
        self.sm.active(0)

    # ---------- Internal ----------
    def update(self):
        """Pull new characters from the PIO and look for beacon messages."""
        got = False
        while self.sm.rx_fifo():
            self.buf += bytes([self.sm.get() >> 24])
            got = True
        if not got:
            return
        now = ticks_ms()
        self.last_byte_ms = now
        self.buf = self.buf[-32:]                  # keep only recent characters
        for msg, color in MESSAGES.items():
            i = self.buf.find(msg)
            if i != -1:
                self.last_seen[color] = now
                self.last_color = color
                self.buf = self.buf[i + len(msg):]

    def _recent(self, t):
        return t is not None and ticks_diff(ticks_ms(), t) < self.timeout_ms

    # ---------- Public ----------
    def sees_signal(self):
        """True if ANY IR data arrived recently (decoded or not)."""
        self.update()
        return self._recent(self.last_byte_ms)

    def read_beacon(self):
        """Most recent beacon decoded: "MAGENTA", "YELLOW", "CYAN", or None."""
        self.update()
        if self.last_color and self._recent(self.last_seen.get(self.last_color)):
            return self.last_color
        return None

    def sees(self, color):
        """True if the given color's beacon was decoded recently.
        Example: ir.sees("CYAN")"""
        self.update()
        return self._recent(self.last_seen.get(color.upper()))

    def sees_team(self):
        """True if YOUR team's beacon (set in Team.py) was decoded recently."""
        color = Team.get_color()
        return color is not None and self.sees(color)

    def raw_text(self):
        """Characters received so far (for debugging)."""
        self.update()
        return "".join(chr(c) if 32 <= c < 127 else "." for c in self.buf)
    def sees_ir(self, window_ms=200):
        """True if the OUT pin flickers at all (any 38 kHz IR, decoded or not)."""
        saw_low = saw_high = False
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < window_ms:
            if self.pin.value() == 0:
                saw_low = True
            else:
                saw_high = True
            if saw_low and saw_high:
                return True
        return False


def find_baud(pin=10, listen_ms=2000):
    """Point the receiver at a beacon and run this. The right speed prints readable text."""
    for baud in (300, 600, 1200, 2400, 4800):
        ir = IRReceiver(pin=pin, baud=baud)
        ir.buf = b""
        start = ticks_ms()
        text = b""
        while ticks_diff(ticks_ms(), start) < listen_ms:
            while ir.sm.rx_fifo():
                text += bytes([ir.sm.get() >> 24])
            sleep_ms(10)
        ir.stop()
        shown = "".join(chr(c) if 32 <= c < 127 else "." for c in text[-40:])
        print("baud %4d -> %s" % (baud, shown))