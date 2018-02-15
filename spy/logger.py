import logging
import logging.handlers
import time

from settings import DATE_FORMAT, LOG_FILE_NAME, LOG_FILE_MAX_SIZE, LOG_FILES_COUNT


def setup_logger():
    logger = logging.getLogger("RaspMonitor")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(threadName)s - %(moduleName)s - "
                                  "%(levelname)s - %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(filename=LOG_FILE_NAME.format(time.strftime(DATE_FORMAT)),
                                                        maxBytes=LOG_FILE_MAX_SIZE, backupCount=LOG_FILES_COUNT)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger.info("Logger initialized")
    return logger


log = setup_logger()
