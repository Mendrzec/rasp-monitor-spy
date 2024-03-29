# Main loop routines are:
#   * User log in/log out - card reading
#   * Machine start stop - consider strategies
#   * Count machine cycles - consider strategies
#   * Calculate cycles per minute - consider strategies
#   * Store/send collected stats
#   * Logs ageing
#
# short interval:
#   - card reading
#   - cycles counting
#
# long interval:
#   - calculate cycles per minute
#   - send data to server
#
# once a minute collected stats are send to server (REST API)

from spy.MFRC522 import MFRC522
from spy.settings import MACHINE_ON_IN, CYCLES_COUNTER_IN, CYCLES_COUNTER_LATCH_IN, DEVICE_STATUS_LED_OUT, \
    CARD_CYCLES_STATUS_LED_OUT, LOG_LOGGER_NAME, IDENTIFICATION_PORT
from spy.postman import Postman
from spy.stat import Stat, Event
from spy.utils import parse_card_id, get_input_state, DeviceStatusIndicator

from http.server import SimpleHTTPRequestHandler

import logging.config
import RPi.GPIO as GPIO
import signal
import socketserver
import threading
import time


log = logging.getLogger(LOG_LOGGER_NAME)


class Spy:
    SLOW_LOOP_INTERVAL = 2.0  # seconds
    STATS_SEND_INTERVAL = 60.0  # seconds
    STATS_SAMPLING_INTERVAL = 60.0  # seconds
    FAST_LOOP_INTERVAL = 0.2  # seconds
    CARD_TIME_OUT = 5.0  # seconds
    CYCLES_IN_BOUNCE_TIME = 75  # miliseconds
    SIXTY_SECONDS = 60  # seconds

    def __init__(self):
        self._mifare = MFRC522()
        self._get_current_time = time.monotonic

        self._stat = Stat()
        self._postman = Postman()

        self._cycles_count_lock = threading.Lock()

        self._machine_on_off = 0
        self._cycles_count = 0
        self._cycles_count_latch = 0
        self._prev_cycles_count = 0
        self._prev_cycles_count_latch = 0
        self._cycles_per_minute = 0
        self._cycles_per_minute_latch = 0

        self._should_fast_loop = True
        self._should_slow_loop = True

        # Sets up simple http server with port 30330
        # It may help to identify if service is running and to find available raspomnitors in a network
        # In the future may be useful to change to show things or edit config through web browser
        self._http_identification_server = socketserver.TCPServer(("", IDENTIFICATION_PORT), SimpleHTTPRequestHandler)

        self._initialize_gpio()
        self._initialize_stop_strategy()

        self.device_status_indicator = DeviceStatusIndicator()

    def _initialize_gpio(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        GPIO.setup(MACHINE_ON_IN, GPIO.IN)
        GPIO.setup(CYCLES_COUNTER_IN, GPIO.IN)
        GPIO.setup(CYCLES_COUNTER_LATCH_IN, GPIO.IN)

        GPIO.setup(CARD_CYCLES_STATUS_LED_OUT, GPIO.OUT)
        GPIO.output(CARD_CYCLES_STATUS_LED_OUT, GPIO.LOW)
        GPIO.setup(DEVICE_STATUS_LED_OUT, GPIO.OUT)
        GPIO.output(DEVICE_STATUS_LED_OUT, GPIO.HIGH)

        GPIO.add_event_detect(CYCLES_COUNTER_IN, GPIO.BOTH, callback=self._machine_cycles_counter_callback,
                              bouncetime=Spy.CYCLES_IN_BOUNCE_TIME)

    def _initialize_stop_strategy(self):
        signal.signal(signal.SIGINT, self._stop_and_clean_callback)
        signal.signal(signal.SIGTERM, self._stop_and_clean_callback)

    def _stop_and_clean_callback(self, signum, frame):
        log.info("Caught shutdown signal ({}), exiting...".format(signum))
        GPIO.remove_event_detect(MACHINE_ON_IN)
        GPIO.remove_event_detect(CYCLES_COUNTER_IN)

        self._should_fast_loop = False
        self._should_slow_loop = False
        self._http_identification_server.shutdown()
        self.device_status_indicator.should_indicate_status_loop = False

    def _machine_cycles_counter_callback(self, channel):
        time.sleep(Spy.CYCLES_IN_BOUNCE_TIME/1000.0)
        if get_input_state(CYCLES_COUNTER_IN):
            if self._stat.card_id != Stat.CARD_ID_NONE:
                GPIO.output(CARD_CYCLES_STATUS_LED_OUT, GPIO.LOW)
            self._cycles_count_lock.acquire()
            self._cycles_count += 1
            if get_input_state(CYCLES_COUNTER_LATCH_IN):
                self._cycles_count_latch += 1
            log.debug("Captured cycle event. Cycles count: {}. Latched cycles count: {}"
                      .format(self._cycles_count, self._cycles_count_latch))
            self._cycles_count_lock.release()
        else:
            if self._stat.card_id != Stat.CARD_ID_NONE:
                GPIO.output(CARD_CYCLES_STATUS_LED_OUT, GPIO.HIGH)

    def _add_events_bundle(self):
        self._stat.add_event(Event.TYPE_MACHINE_ON_OFF, self._machine_on_off)
        self._stat.add_event(Event.TYPE_CYCLES_COUNT, self._cycles_count)
        self._stat.add_event(Event.TYPE_CYCLES_COUNT_LATCH, self._cycles_count_latch)
        self._stat.add_event(Event.TYPE_CYCLES_PER_MINUTE, self._cycles_per_minute)
        self._stat.add_event(Event.TYPE_CYCLES_PER_MINUTE_LATCH, self._cycles_per_minute_latch)

    def _reset_local_stats(self):
        self._cycles_count = 0
        self._cycles_count_latch = 0
        self._prev_cycles_count = 0
        self._prev_cycles_count_latch = 0
        self._cycles_per_minute = 0
        self._cycles_per_minute_latch = 0

    def _fresh_stat(self, card_id):
        self._add_events_bundle()
        self._postman.safe_queue_append(self._stat.dump_and_clean().copy())

        self._reset_local_stats()
        self._stat = Stat(card_id)

    def _compute_cycles_per_minute(self, current_time, cpm_compute_time_stamp):
        self._cycles_count_lock.acquire()
        delta_time = current_time - cpm_compute_time_stamp

        delta_cycles = self._cycles_count - self._prev_cycles_count
        self._prev_cycles_count = self._cycles_count
        self._cycles_per_minute = delta_cycles / delta_time * Spy.SIXTY_SECONDS
        log.debug("Cycles per minute: {}".format(self._cycles_per_minute))

        delta_cycles_latch = self._cycles_count_latch - self._prev_cycles_count_latch
        self._prev_cycles_count_latch = self._cycles_count_latch
        self._cycles_per_minute_latch = delta_cycles_latch / delta_time * Spy.SIXTY_SECONDS
        log.debug("Cycles per minute latch: {}".format(self._cycles_per_minute_latch))
        self._cycles_count_lock.release()

    def _fast_loop(self):
        card_read_time_stamp = self._get_current_time()
        while self._should_fast_loop:
            time.sleep(Spy.FAST_LOOP_INTERVAL)

            status, _ = self._mifare.MFRC522_Request(MFRC522.PICC_REQIDL)
            if status != MFRC522.MI_OK:  # card not found
                if ((self._get_current_time() - card_read_time_stamp) > Spy.CARD_TIME_OUT
                        and self._stat.card_id != Stat.CARD_ID_NONE):
                    log.info("Card {} timeouted".format(self._stat.card_id))
                    GPIO.output(CARD_CYCLES_STATUS_LED_OUT, GPIO.LOW)  # indicate that card has been read
                    self._fresh_stat(Stat.CARD_ID_NONE)
                continue

            status, uid = self._mifare.MFRC522_Anticoll()
            if status != MFRC522.MI_OK:  # could not retrieve uid -> continue
                continue

            parsed_uid = parse_card_id(uid)
            card_read_time_stamp = self._get_current_time()
            if parsed_uid != self._stat.card_id:  # card id has changed
                log.info("Read new card {}".format(parsed_uid))
                GPIO.output(CARD_CYCLES_STATUS_LED_OUT, GPIO.HIGH)  # indicate that card has been read
                self._fresh_stat(parsed_uid)

    def _slow_loop(self):
        current_time = self._get_current_time()
        stats_sampled_time_stamp = current_time
        stats_sent_time_stamp = current_time

        stats_send_thread = None
        previous_machine_on_off = None

        while self._should_slow_loop:
            # machine state detection
            self._machine_on_off = get_input_state(MACHINE_ON_IN)
            if self._machine_on_off != previous_machine_on_off:
                self._stat.add_event(Event.TYPE_MACHINE_ON_OFF, self._machine_on_off)
                previous_machine_on_off = self._machine_on_off
                log.debug("Captured machine_on_off event. Value: {}".format(self._machine_on_off))

            # compute cycles per minute and add stats to queue
            # - adjust the STATS_TO_QUEUE_INTERVAL to set stats resolution
            current_time = self._get_current_time()
            if (current_time - stats_sampled_time_stamp) > Spy.STATS_SAMPLING_INTERVAL:
                log.debug("Going to compute cycles per minute...")
                self._compute_cycles_per_minute(current_time, stats_sampled_time_stamp)
                # cycles per minute accuracy depends on this time stamp
                stats_sampled_time_stamp = self._get_current_time()

                log.debug("Going to add stats to send queue...")
                self._add_events_bundle()
                self._postman.safe_queue_append(self._stat.dump_and_clean().copy())

            # send stats collected in send queue
            current_time = self._get_current_time()
            if (current_time - stats_sent_time_stamp) > Spy.STATS_SEND_INTERVAL:
                log.debug("Going to send some collected stats...")
                stats_sent_time_stamp = current_time

                if stats_send_thread is not None and stats_send_thread.is_alive():
                    log.error("Stats sending thread '{}' is still alive!".format(stats_send_thread.getName()))
                else:
                    stats_send_thread = threading.Thread(target=self._postman.send_data)
                    stats_send_thread.start()

            time.sleep(Spy.SLOW_LOOP_INTERVAL)

    def launch(self):
        device_status_indicator_thread = threading.Thread(target=self.device_status_indicator.indicate_status)
        fast_loop_thread = threading.Thread(target=self._fast_loop)
        slow_loop_thread = threading.Thread(target=self._slow_loop)
        http_identification_server_thread = threading.Thread(target=self._http_identification_server.serve_forever)

        device_status_indicator_thread.start()
        fast_loop_thread.start()
        slow_loop_thread.start()
        http_identification_server_thread.start()

        device_status_indicator_thread.join()
        fast_loop_thread.join()
        slow_loop_thread.join()
        http_identification_server_thread.join()

        GPIO.cleanup()
