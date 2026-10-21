# pyright: reportUndefinedVariable=false
# ECE 3331 Recycling Rover - IR beacon emitter (Raspberry Pi Pico, MicroPython)
#
# Wiring:
#   GP18 (physical pin 24) -> 150-220 ohm resistor -> SFH 4545 anode (long leg)
#   SFH 4545 cathode (short leg) -> GND
#
# Sends one team message over and over on a 38 kHz carrier, as UART 8N1:
# a 0 bit = 38 kHz IR burst, a 1 bit / idle = IR off.
#
# Use it from another file:
#     from ir_emitter import IREmitter
#     tx = IREmitter(color="CYAN")
#     while True:
#         tx.update()          # call often; it sends on its own schedule
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

BAUD = 2400             # carrier works out to 38.7 kHz at this rate

# Each bit = 16 carrier cycles, each carrier cycle = 32 PIO instructions,
# plus 4 instructions of overhead per bit.
TX_SM_FREQ = (32 * 16 + 4) * BAUD


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_RIGHT,
             fifo_join=rp2.PIO.JOIN_TX)
def ir_uart_tx():
    # Each word pulled = 10 bits, LSB first: start(0), 8 data bits, stop(1).
    wrap_target()
    pull(block)
    set(x, 9)
    label("bitloop")
    out(y, 1)
    jmp(not_y, "mark")
    set(y, 15)
    label("space")              # 1 bit: IR off for 16 carrier periods
    nop()                 [30]
    jmp(y_dec, "space")
    jmp(x_dec, "bitloop")
    jmp("done")
    label("mark")               # 0 bit: 16 cycles of 38 kHz carrier
    set(y, 15)
    label("on")
    set(pins, 1)          [15]
    set(pins, 0)          [14]
    jmp(y_dec, "on")
    jmp(x_dec, "bitloop")
    label("done")
    wrap()


class IREmitter:
    def __init__(self, pin=18, color="CYAN", gap_ms=100, sm_id=0,
                 led=None, verbose=True):
        # pin=18 is GP18 (physical pin 24). The TX FIFO is joined to 8 words,
        # so a whole 7-character message fits and send() never blocks.
        self.pin_num = pin
        self.gap_ms = gap_ms
        self.led = led
        self.verbose = verbose
        self.count = 0
        self.sm = rp2.StateMachine(sm_id, ir_uart_tx, freq=TX_SM_FREQ,
                                   set_base=Pin(pin))
        self.sm.active(1)
        self.color = None
        self.set_color(color)
        self._next_send = time.ticks_ms()

    def set_color(self, color):
        color = color.upper()
        if color not in MESSAGES:
            raise ValueError("color must be MAGENTA, YELLOW or CYAN")
        self.color = color
        self.message = MESSAGES[color]
        self.frame_ms = len(self.message) * 10 * 1000 // BAUD  # ~29 ms
        if self.verbose:
            print("[TX] sending", color, "->", repr(self.message))

    def send(self, text=None):
        # Queue one message for the PIO to transmit. Returns immediately.
        for ch in (text or self.message):
            self.sm.put((ord(ch) << 1) | (1 << 9))  # start 0, data, stop 1
        self.count += 1

    def update(self):
        # Non-blocking: sends the message again once the previous one plus
        # the gap has finished. Call this as often as you like.
        now = time.ticks_ms()
        if time.ticks_diff(now, self._next_send) < 0:
            return
        if self.led:
            self.led.toggle()
        self.send()
        self._next_send = time.ticks_add(now, self.frame_ms + self.gap_ms)
        if self.verbose and self.count % 10 == 0:
            print("[TX]   sent {!r} x{}".format(self.message, self.count))

    def stop(self):
        self.sm.active(0)
        Pin(self.pin_num, Pin.OUT).value(0)   # make sure the IR LED is off
        if self.led:
            self.led.off()


# ---------------------------------------------------------------- standalone

if __name__ == "__main__":
    import sys
    import select

    KEYS = {"m": "MAGENTA", "y": "YELLOW", "c": "CYAN"}
    tx = IREmitter(color="CYAN", led=Pin("LED", Pin.OUT))
    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)
    print("IR emitter on GP18 (pin 24), {} baud, {:.1f} kHz carrier".format(
        BAUD, TX_SM_FREQ / 32 / 1000))
    print("Type m, y or c then Enter to switch colors. Ctrl+C to stop.\n")
    try:
        while True:
            if poller.poll(0):
                ch = sys.stdin.read(1).lower()
                if ch in KEYS:
                    tx.set_color(KEYS[ch])
            tx.update()
            time.sleep_ms(2)
    except KeyboardInterrupt:
        tx.stop()
        print("\nStopped.")