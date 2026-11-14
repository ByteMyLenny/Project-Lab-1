# Main.py: color sensor test
import ColorSensor as cs        # must match the file name exactly (ColorSensor.py)
from utime import sleep

# 1) Raw check: are we getting readings at all?
print("Raw check (Hz). Wave something under the sensor:")
for _ in range(5):
    print("R:", int(cs.read_filter("red")),
          " G:", int(cs.read_filter("green")),
          " B:", int(cs.read_filter("blue")),
          " Clear:", int(cs.read_filter("clear")))
    sleep(0.5)

# 2) White calibration (for this run)
print("Hold WHITE paper under the sensor...")
sleep(3)
cs.calibrate_white()

# 3) Live readings
print("Now hold washers under it:")
while True:
    r, g, b = cs.read_rgb()
    clear = cs.read_filter("clear")
    print("R:%.2f G:%.2f B:%.2f  Clear:%d  ->  %s" % (r, g, b, clear, cs.classify()))
    sleep(0.5)