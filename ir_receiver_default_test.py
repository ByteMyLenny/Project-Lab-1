# TSOP38238 receiver test with any IR remote (Raspberry Pi Pico, MicroPython)
#
# Wiring (TSOP38238, dome facing you, leads down, pins 1-2-3 left to right):
#   pin 1 OUT -> GP15 (physical pin 20)
#   pin 2 GND -> GND
#   pin 3 VS  -> 3.3 V
#
# Point a TV/AC/any IR remote at the receiver and press buttons.
# The onboard LED lights whenever IR is being received.

from machine import Pin
import time

r = Pin(15, Pin.IN, Pin.PULL_UP)
led = Pin("LED", Pin.OUT)

edges = 0
last_edge = time.ticks_ms()


def on_edge(pin):
    global edges, last_edge
    edges += 1
    last_edge = time.ticks_ms()


r.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=on_edge)

print("Receiver test on GP15. Idle reading:", r.value(), "(should be 1)")
if r.value() == 0:
    print("WARNING: output is stuck LOW - check VS / GND wiring")
print("Press buttons on your remote...\n")

presses = 0
last_status = time.ticks_ms()

try:
    while True:
        led.value(r.value() == 0)   # LED on while IR is being seen

        # A button press is finished once there's been 100 ms of silence
        if edges and time.ticks_diff(time.ticks_ms(), last_edge) > 100:
            n = edges
            edges = 0
            presses += 1
            if n >= 10:
                print("#{}  IR RECEIVED - {} edges  -> receiver works!".format(presses, n))
            else:
                print("#{}  short blip ({} edges) - probably noise or weak signal".format(presses, n))

        # Heartbeat every 3 s so you know it's still running
        if time.ticks_diff(time.ticks_ms(), last_status) > 3000:
            print("  ...waiting (output = {})".format(r.value()))
            last_status = time.ticks_ms()

        time.sleep_ms(5)
except KeyboardInterrupt:
    led.off()
    print("\nStopped.")