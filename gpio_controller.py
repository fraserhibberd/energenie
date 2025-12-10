import atexit
import logging
import time

import RPi.GPIO as GPIO


LOGGER = logging.getLogger(__name__)

class EnergenieGPIO:
    _PIN_K = (11, 15, 16, 13)
    _PIN_MODSEL = 18
    _PIN_ENABLE = 22
    _SETTLE_SECONDS = 0.1
    _TRANSMIT_SECONDS = 0.25

    _ON_CODES = {
        1: (True, True, True, True),
        2: (False, True, True, True),
        3: (True, False, True, True),
        4: (False, False, True, True),
    }

    _OFF_CODES = {
        1: (True, True, True, False),
        2: (False, True, True, False),
        3: (True, False, True, False),
        4: (False, False, True, False),
    }

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        for pin in self._PIN_K:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)
        GPIO.setup(self._PIN_MODSEL, GPIO.OUT)
        GPIO.setup(self._PIN_ENABLE, GPIO.OUT)
        GPIO.output(self._PIN_ENABLE, False)
        GPIO.output(self._PIN_MODSEL, False)
        atexit.register(GPIO.cleanup)

    def turn_on(self, receiver):
        LOGGER.info('Turning receiver %d ON', receiver)
        self._send_code(self._bits_for(receiver, self._ON_CODES))

    def turn_off(self, receiver):
        LOGGER.info('Turning receiver %d OFF', receiver)
        self._send_code(self._bits_for(receiver, self._OFF_CODES))

    @staticmethod
    def _bits_for(receiver, mapping):
        try:
            return mapping[int(receiver)]
        except (ValueError, KeyError):
            raise ValueError('Receiver must be an integer 1-4')

    def _send_code(self, bits):
        LOGGER.debug('Sending code: %s', bits)
        for pin, value in zip(self._PIN_K, bits):
            GPIO.output(pin, value)
        time.sleep(self._SETTLE_SECONDS)
        GPIO.output(self._PIN_ENABLE, True)
        time.sleep(self._TRANSMIT_SECONDS)
        GPIO.output(self._PIN_ENABLE, False)
