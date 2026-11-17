import IR_Receiver as irr, ProximitySensors as ps, ColorSensor as cs, MotorDriver as driver, Servo as servo, Team
from utime import sleep_ms

ir = irr.IRReceiver(pin=9)

while True:
    print("Raw IR: ", ir.sees_ir(), "Formated Signal: ", ir.sees_signal())
    sleep_ms(200)