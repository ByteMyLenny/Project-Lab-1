# DEBUG_MOTORDRIVER.py: For Basic Testing/Debugging. A playground.
import MotorDriver as driver
from utime import sleep_ms


driver.movement("F", driver.SPEED )
sleep_ms(3000)
driver.movement("S")