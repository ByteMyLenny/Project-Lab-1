from MotorDriver import movement
import Reflectance_Sensor as rs
from utime import sleep

#Don't Forget To Run CALIBRATE_Tape.py For The Tape!!!
left, right = rs.tape_sides()

rs.calibrate()
while True:
    print(rs.read_all())
    sleep(0.5)
    if left or right:
        print("TAPE!")
