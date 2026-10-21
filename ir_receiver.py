# pyright: reportUndefinedVariable=false
# ECE 3331 Recycling Rover - IR beacon receiver (Raspberry Pi Pico, MicroPython)
#
# Wiring (TSOP38238):
#   pin 1 OUT -> GP15 (physical pin 20)
#   pin 2 VCC -> 3V3 OUT (physical pin 36)
#   pin 3 GND -> GND
#
# Decodes MAGENTA / YELLOW_ / CYAN___ sent as UART 8N1 on a 38 kHz carrier
# (same format as ir_emitter.py).
#
# Use it from another file:
#     from ir_receiver import IRReceiver
#     rx = IRReceiver(target="CYAN")
#     while True:
#         color = rx.update()   # "MAGENTA"/"YELLOW"/"CYAN" when one arrives, else None
#         if rx.sees_target():  # True while the target beacon is being heard
#             ...
#
# Or run this file directly to test it alone (type m / y / c + Enter to switch).

import rp2
import time
from machine import Pin

MESSAGES = {
    "MAGENTA": "MAGENTA",   # 4D 41 47 45 4E 54 41
    "YELLOW":  "YELLOW_",   # 59 45 4C 4C 4F 57 5F
    "CYAN":    "CYAN___",   # 43 59 41 4E 5F 5F 5F
}
COLOR_OF = {msg: color for color, msg in MESSAGES.items()}

BAUD = 2400             # must match the emitter / beacon


@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_RX)
def uart_rx():
    # Standard 8N1 receiver, runs at 8 ticks per bit.
    # TSOP output idles HIGH and goes LOW during an IR burst, so a
    # burst = 0 bit and no IR = 1 bit, just like a normal UART line.
    label("start")
    wait(0, pin, 0)               # start bit: output goes LOW
    set(x, 7)             [10]    # skip to the middle of data bit 0
    label("bitloop")
    in_(pins, 1)                  # sample one bit
    jmp(x_dec, "bitloop") [6]     # 8 ticks per bit
    jmp(pin, "good_stop")         # stop bit must be HIGH
    wait(1, pin, 0)               # framing error: wait for idle, drop byte
    jmp("start")
    label("good_stop")
    push(block)                   # hand the byte to Python


class IRReceiver:
    def __init__(self, pin=15, target="CYAN", sm_id=1, lost_ms=1000,
                 led=None, verbose=True):
        # pin=15 is GP15 (physical pin 20).
        self.lost_ms = lost_ms
        self.led = led
        self.verbose = verbose
        rx_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.sm = rp2.StateMachine(sm_id, uart_rx, freq=8 * BAUD,
                                   in_base=rx_pin, jmp_pin=rx_pin)
        self.sm.active(1)

        self.target = None
        self.set_target(target)
        self.last_color = None        # last valid message heard
        self.last_heard = time.ticks_ms()
        self.received = 0             # total valid messages
        self._window = ""
        self._junk = 0
        self._repeats = 0
        self._lost_reported = False

    def set_target(self, color):
        color = color.upper()
        if color not in MESSAGES:
            raise ValueError("target must be MAGENTA, YELLOW or CYAN")
        self.target = color
        if self.verbose:
            print("[RX] looking for", color, "->", repr(MESSAGES[color]))

    def has_signal(self):
        # True if any valid message arrived within lost_ms.
        return (self.last_color is not None and
                time.ticks_diff(time.ticks_ms(), self.last_heard) < self.lost_ms)

    def sees_target(self):
        # True while the target beacon is currently being heard.
        return self.has_signal() and self.last_color == self.target

    def update(self):
        # Non-blocking: reads whatever bytes the PIO has collected.
        # Returns the color of a message completed during this call, or None.
        got = None
        while self.sm.rx_fifo():
            ch = chr(self.sm.get() >> 24)
            self._window = (self._window + ch)[-7:]
            if self._window not in COLOR_OF:
                self._junk += 1
                continue

            color = COLOR_OF[self._window]
            self._window = ""
            self._junk = 0
            self._lost_reported = False
            self.last_heard = time.ticks_ms()
            self.received += 1
            got = color

            if color == self.last_color:
                self._repeats += 1
            else:
                self.last_color, self._repeats = color, 0
            if self.verbose and self._repeats % 10 == 0:
                print("[RX] {:<8} {!r}  {}{}".format(
                    color, MESSAGES[color],
                    "<-- MATCH" if color == self.target else "(not target)",
                    "  x{}".format(self._repeats) if self._repeats else ""))

        # Bytes arriving but no valid message = wrong baud or bad signal
        if self._junk > 30:
            if self.verbose:
                print("[RX]   receiving garbage, last chars:", repr(self._window),
                      "- check baud rate / aim / distance")
            self._junk = 0

        if (not self._lost_reported and
                time.ticks_diff(time.ticks_ms(), self.last_heard) > self.lost_ms):
            if self.verbose:
                print("[RX]   no signal")
            self.last_color = None
            self._lost_reported = True

        if self.led:
            self.led.value(self.sees_target())
        return got

    def stop(self):
        self.sm.active(0)
        if self.led:
            self.led.off()


# ---------------------------------------------------------------- standalone

if __name__ == "__main__":
    import sys
    import select

    KEYS = {"m": "MAGENTA", "y": "YELLOW", "c": "CYAN"}
    rx = IRReceiver(target="CYAN", led=Pin("LED", Pin.OUT))
    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)
    print("IR receiver on GP15 (pin 20), {} baud".format(BAUD))
    print("Type m, y or c then Enter to change target. Ctrl+C to stop.\n")
    try:
        while True:
            if poller.poll(0):
                ch = sys.stdin.read(1).lower()
                if ch in KEYS:
                    rx.set_target(KEYS[ch])
            rx.update()
            time.sleep_ms(2)
    except KeyboardInterrupt:
        rx.stop()
        print("\nStopped.")