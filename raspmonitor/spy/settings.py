import time

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

SERVER_URL = "http://192.168.0.165:8000/"

STATS_NOT_SENT_DIR = "stats_not_sent/"
STATS_NOT_SENT_FILE_NAME = STATS_NOT_SENT_DIR + "stats.json"

LOG_DIR = "logs/"
LOG_FILE_NAME = LOG_DIR + "raspmonitor_spy_{}.log"
LOG_FILE_MAX_SIZE = 10*1024*1024
LOG_FILES_COUNT = 5
LOG_LOGGER_NAME = 'rasp_monitor'
LOG_DATE_FORMAT = "%Y%m%d_%H%M%S"

LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(name)s - %(module)s - %(threadName)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_NAME.format(time.strftime(LOG_DATE_FORMAT)),
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILES_COUNT,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        LOG_LOGGER_NAME: {
            'handlers': ['console', 'file'],
            'level': 'DEBUG'
        }
    }
}

IDENTIFICATION_PORT = 30330

# Board index
MACHINE_ON_IN = 40  # 21
CYCLES_PER_MINUTE_IN = 37  # not used
CYCLES_COUNTER_IN = 38  # 20
CYCLES_COUNTER_LATCH_IN = 35  # 19
ADDITIONAL_IN_0 = 36
ADDITIONAL_IN_1 = 33

CARD_IN_LED_OUT = 32  # turn on to show user is properly loged in
CYCLES_COUNTING_LED_OUT = 29  # turn on to show each cycles is captured
ADDITIONAL_OUT_0 = 31
