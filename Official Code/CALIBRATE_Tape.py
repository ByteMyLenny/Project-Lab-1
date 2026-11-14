import Reflectance_Sensor as rs
from utime import sleep

rs.calibrate()
while True:
    print(rs.read_all())
    sleep(0.5)