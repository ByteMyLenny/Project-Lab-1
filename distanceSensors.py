from machine import Pin, ADC

sensor = ADC(Pin(26))  # GP26 = ADC0

while True:
    raw = sensor.read_u16()
    voltage = raw * 3.3 / 65535
    
    distance_cm = 32.14 / (voltage - 0.386)
    
    print(f"{voltage:.2f}V -> {distance_cm:.1f} cm")