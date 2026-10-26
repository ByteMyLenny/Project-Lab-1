from machine import Pin, PWM
import time

# =====================================
# MOTOR 1 - L293D
# =====================================
en1 = PWM(Pin(14))
in1 = Pin(15, Pin.OUT)
in2 = Pin(16, Pin.OUT)

# =====================================
# MOTOR 2 - L293D
# =====================================
en2 = PWM(Pin(20))
in3 = Pin(18, Pin.OUT)
in4 = Pin(19, Pin.OUT)

# =====================================
# PWM SPEED SETTINGS
# =====================================
en1.freq(1000)
en2.freq(1000)

STARTUP_SPEED = 100  # 100% PWM
DRIVE_SPEED = 55     # 60% PWM
BOOST_TIME = 0.2     # 0.2 seconds

startup_duty = int(STARTUP_SPEED / 100 * 65535)
drive_duty = int(DRIVE_SPEED / 100 * 65535)

# =====================================
# METAL DETECTOR - GP17
# =====================================
metal = Pin(17, Pin.IN, Pin.PULL_UP)

# 0 = Metal detected
# 1 = No metal detected

# =====================================
# STOP FUNCTION
# =====================================
def stop():
    en1.duty_u16(0)
    en2.duty_u16(0)

    in1.value(0)
    in2.value(0)
    in3.value(0)
    in4.value(0)

# =====================================
# MAIN PROGRAM
# =====================================

# Start safely
stop()
time.sleep(1)

# Check if metal is already detected
if metal.value() == 0:
    print("Metal already detected!")
    stop()

else:
    # Set both motors forward
    in1.value(1)
    in2.value(0)

    in3.value(1)
    in4.value(0)

    # =================================
    # STARTUP BOOST - 100% PWM
    # =================================
    print("Startup boost: 100% PWM")

    en1.duty_u16(startup_duty)
    en2.duty_u16(startup_duty)

    # Check sensor during startup boost
    start_time = time.ticks_ms()

    while time.ticks_diff(
        time.ticks_ms(), start_time
    ) < int(BOOST_TIME * 1000):

        if metal.value() == 0:
            break

        time.sleep_ms(5)

    # =================================
    # NORMAL DRIVE - 60% PWM
    # =================================
    if metal.value() == 1:

        en1.duty_u16(drive_duty)
        en2.duty_u16(drive_duty)

        print("Driving at 60% PWM")
        print("Searching for metal...")

        # Continue until metal detected
        while metal.value() == 1:
            time.sleep_ms(5)

    # =================================
    # METAL DETECTED - STOP
    # =================================
    stop()

    print("METAL DETECTED!")
    print("Both motors stopped.")
    print("Program ended.")
