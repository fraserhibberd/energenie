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

    def __init__(self, receiver_socket: int):
        self._receiver_socket = self._validate_receiver(receiver_socket)
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

    def turn_on(self):
        LOGGER.info('Turning receiver %d ON', self._receiver_socket)
        self._send_code(self._bits_for(self._receiver_socket, self._ON_CODES))

    def turn_off(self):
        LOGGER.info('Turning receiver %d OFF', self._receiver_socket)
        self._send_code(self._bits_for(self._receiver_socket, self._OFF_CODES))

    @staticmethod
    def _bits_for(receiver, mapping):
        try:
            return mapping[int(receiver)]
        except (ValueError, KeyError):
            raise ValueError('Receiver must be an integer 1-4')

    @staticmethod
    def _validate_receiver(receiver):
        try:
            receiver_int = int(receiver)
        except (TypeError, ValueError):
            raise ValueError('Receiver must be an integer 1-4')
        if receiver_int not in (1, 2, 3, 4):
            raise ValueError('Receiver must be an integer 1-4')
        return receiver_int

    def _send_code(self, bits):
        LOGGER.debug('Sending code: %s', bits)
        for pin, value in zip(self._PIN_K, bits):
            GPIO.output(pin, value)
        time.sleep(self._SETTLE_SECONDS)
        GPIO.output(self._PIN_ENABLE, True)
        time.sleep(self._TRANSMIT_SECONDS)
        GPIO.output(self._PIN_ENABLE, False)
