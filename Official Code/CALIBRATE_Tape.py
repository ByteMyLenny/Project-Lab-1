import Reflectance_Sensor as rs
from utime import sleep

while True:
    print(rs.read_all())
    sleep(0.5)