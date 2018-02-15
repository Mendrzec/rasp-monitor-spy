import RPi.GPIO as GPIO

from logger import log
from settings import MACHINE_ON_IN, CYCLES_COUNTER_IN, CYCLES_COUNTER_LATCH_IN, USER_LOG_IN_LED_OUT, \
    CYCLES_COUNTING_LED_OUT


def init() -> None:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    GPIO.setup(MACHINE_ON_IN, GPIO.IN)  # work time recording
    GPIO.setup(CYCLES_COUNTER_IN, GPIO.IN)  # machine cycles counter
    GPIO.setup(CYCLES_COUNTER_LATCH_IN, GPIO.IN)  # latch to machine cycles counter

    GPIO.setup(USER_LOG_IN_LED_OUT, GPIO.OUT)  # user loged in LED
    GPIO.output(USER_LOG_IN_LED_OUT, GPIO.LOW)
    GPIO.setup(CYCLES_COUNTING_LED_OUT,GPIO.OUT)  # cycles counting LED
    GPIO.output(CYCLES_COUNTING_LED_OUT, GPIO.LOW)
    log.info("GPIO initialized")


def clean() -> None:
    GPIO.cleanup()


def get_input(input_: int) -> bool:
    if GPIO.input(input_) == GPIO.LOW:
        return True
    return False



