# Main loop routines are:
#   * User log in/log out - card reading
#   * Machine start stop - consider strategies
#   * Count machine cycles - consider strategies
#   * Calculate cycles per minute - consider strategies
#   * Store/send collected stats
#   * Logs ageing
#   *

import signal

from MFRC522 import MFRC522
import gpio_utils


class Spy:
    def __init__(self):
        self.mifare_reader = MFRC522.MFRC522()

    def main_loop(self):
        pass


def close_handle():
    gpio_utils.clean()


gpio_utils.init()

# PROGRAM

signal.signal(signal.SIGINT, close_handle())
