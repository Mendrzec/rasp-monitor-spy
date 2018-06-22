from spy.settings import LOG_CONFIG, LOG_LOGGER_NAME
from spy.spy import Spy

import logging.config

logging.config.dictConfig(LOG_CONFIG)
log = logging.getLogger(LOG_LOGGER_NAME)

s = Spy()
s.launch()
