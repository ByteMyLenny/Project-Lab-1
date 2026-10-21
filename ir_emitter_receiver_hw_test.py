from machine import Pin, PWM
import time
tx = PWM(Pin(18)); tx.freq(38000); tx.duty_u16(0)
r = Pin(15, Pin.IN, Pin.PULL_UP)
for i in range(20):
    tx.duty_u16(32768); time.sleep_ms(1); on = r.value()
    tx.duty_u16(0);     time.sleep_ms(3); off = r.value()
    print("IR on:", on, "  IR off:", off)
    time.sleep_ms(200)