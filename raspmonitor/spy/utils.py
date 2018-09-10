from spy.settings import DEVICE_STATUS_LED_OUT

from enum import Enum

import RPi.GPIO as GPIO
import time
import threading


def parse_card_id(card_id: []) -> str:
    return str(card_id[0]) + "." + str(card_id[1]) + "." + str(card_id[2]) + "." + str(card_id[3])


def get_input_state(input_: int) -> int:
    if GPIO.input(input_) == GPIO.LOW:
        return 1
    return 0


class DeviceStatus(Enum):
    DEVICE_HEALTHY = (0, 0.5)
    LOW_SEVERITY_MALFUNCTION = (1, 1)
    HIGH_SEVERITY_MALFUNCTION = (2, 0.25)

    def __init__(self, priority, interval):
        self.priority = priority
        self.interval = interval

    @staticmethod
    def get(priority):
        for item in DeviceStatus:
            if priority == item.priority:
                return item


class DeviceStatusIndicator:
    __instance = None
    __init_complete = False

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        if not DeviceStatusIndicator.__init_complete:
            DeviceStatusIndicator.__init_complete = True

            self.should_indicate_status_loop = True
            self._device_status_lock = threading.Lock()
            self._statuses_to_indicate = {}

    @staticmethod
    def indicate_led(interval, blink=True):
        if blink:
            GPIO.output(DEVICE_STATUS_LED_OUT, GPIO.LOW)
            time.sleep(interval)
        GPIO.output(DEVICE_STATUS_LED_OUT, GPIO.HIGH)
        time.sleep(interval)

    def safe_indicate(self, caller: str, status: DeviceStatus):
        self._device_status_lock.acquire()
        key = caller + str(status.priority)
        self._statuses_to_indicate.update({key: status})
        self._device_status_lock.release()

    def safe_reset(self, caller: str, status: DeviceStatus):
        self._device_status_lock.acquire()
        key = caller + str(status.priority)
        self._statuses_to_indicate.pop(key, None)
        self._device_status_lock.release()

    def _safe_get_status(self) -> DeviceStatus:
        self._device_status_lock.acquire()

        highest_priority = 0
        for status in self._statuses_to_indicate.values():
            if status.priority > highest_priority:
                highest_priority = status.priority
        result = DeviceStatus.get(highest_priority)

        self._device_status_lock.release()
        return result

    def indicate_status(self):
        while self.should_indicate_status_loop:
            status = self._safe_get_status()
            blink = status != DeviceStatus.DEVICE_HEALTHY
            self.indicate_led(status.interval, blink)
