# ECE 3331 Recycling Rover - run the IR emitter and receiver together
#
# Needs ir_emitter.py and ir_receiver.py saved ON THE PICO (same folder).
# Point the SFH 4545 (GP18 / pin 24) at the TSOP38238 (GP15 / pin 20),
# 1-3 ft apart, and run this file.
#
# Keys (type, then press Enter):
#   m / y / c   change what the EMITTER sends
#   M / Y / C   change what the RECEIVER is looking for (shift = receiver)
#   s           print a pass/fail summary
#
# Onboard LED = receiver currently hearing its target.

import sys
import time
import select
from machine import Pin

from ir_emitter import IREmitter
from ir_receiver import IRReceiver

EMIT_COLOR = "CYAN"
TARGET_COLOR = "CYAN"

KEYS = {"m": "MAGENTA", "y": "YELLOW", "c": "CYAN"}

tx = IREmitter(pin=18, color=EMIT_COLOR, sm_id=0)
rx = IRReceiver(pin=15, target=TARGET_COLOR, sm_id=1,
                led=Pin("LED", Pin.OUT))

poller = select.poll()
poller.register(sys.stdin, select.POLLIN)


def summary():
    sent, got = tx.count, rx.received
    rate = 100 * got // sent if sent else 0
    print("\n[TEST] sent {}  received {}  ({}%)  emitter={}  target={}  {}\n".format(
        sent, got, rate, tx.color, rx.target,
        "MATCH" if rx.sees_target() else "no match"))


print("IR loopback test: emitter GP18 (pin 24) -> receiver GP15 (pin 20)")
print("m/y/c = emitter color, M/Y/C = receiver target, s = summary, Ctrl+C = stop\n")

try:
    while True:
        if poller.poll(0):
            ch = sys.stdin.read(1)
            if ch.lower() in KEYS:
                if ch.isupper():
                    rx.set_target(KEYS[ch.lower()])
                else:
                    tx.set_color(KEYS[ch])
            elif ch == "s":
                summary()

        tx.update()
        rx.update()
        time.sleep_ms(2)
except KeyboardInterrupt:
    tx.stop()
    rx.stop()
    summary()
    print("Stopped.")