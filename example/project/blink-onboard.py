import machine
import time

pin = machine.Pin(2, mode=machine.Pin.OUT)

while True:
    pin.value(not pin.value())
    print(pin, '->', pin.value())
    time.sleep(1)
