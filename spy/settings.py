DATE_FORMAT = "%Y%m%d_%H%M%S"

LOG_DIR = "logs/"
LOG_FILE_NAME = LOG_DIR + "raspMonitorSpy_{}.log"
LOG_FILE_MAX_SIZE = 10*1024*1024
LOG_FILES_COUNT = 5

# Board index
MACHINE_ON_IN = 40
CYCLES_PER_MINUTE_IN = 37  # not used
CYCLES_COUNTER_IN = 38
CYCLES_COUNTER_LATCH_IN = 35
ADDITIONAL_IN_0 = 36
ADDITIONAL_IN_1 = 33

USER_LOG_IN_LED_OUT = 32  # turn on to show user is properly loged in
CYCLES_COUNTING_LED_OUT = 29  # turn on to show each cycles is captured
ADDITIONAL_OUT_0 = 31
