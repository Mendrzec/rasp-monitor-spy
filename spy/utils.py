import RPi.GPIO as GPIO


def parse_card_id(card_id: []) -> str:
    return str(card_id[0]) + "." + str(card_id[1]) + "." + str(card_id[2]) + "." + str(card_id[3])


def get_input_state(input_: int) -> int:
    if GPIO.input(input_) == GPIO.LOW:
        return 1
    return 0
