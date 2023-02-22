from .lib import unittest
import machine

class TestPin(unittest.TestCase):

    def test_pin_on(self):
        pin = machine.Pin(2, mode=machine.Pin.OUT)
        pin.value(1)
        self.assertEqual(pin.value(), 1)

    def test_pin_off(self):
        pin = machine.Pin(2, mode=machine.Pin.OUT)
        pin.value(0)
        self.assertEqual(pin.value(), 0)

    def test_pin_toggle(self):
        pin = machine.Pin(2, mode=machine.Pin.OUT)
        pin.value(0)
        self.assertEqual(pin.value(), 0)
        pin.value(not pin.value())
        self.assertEqual(pin.value(), 1)