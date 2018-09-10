from spy.settings import LOG_LOGGER_NAME, STATS_NOT_SENT_FILE_NAME, SERVER_URL
from spy.postman_filehelper import PostmanFileHelper
from spy.utils import DeviceStatusIndicator, DeviceStatus
from threading import Lock

import logging
import requests


log = logging.getLogger(LOG_LOGGER_NAME)
ds_indicator = DeviceStatusIndicator()


class Postman(PostmanFileHelper):
    MAX_RETRIES = 3
    MAX_STATS_FROM_FILE = 25
    HEADERS = {'Content-type': 'application/json'}

    def __init__(self, server_url=SERVER_URL, base_file_path=STATS_NOT_SENT_FILE_NAME):
        super(Postman, self).__init__(base_file_path)
        self.server_url = server_url

        self._lock = Lock()
        self._queue = []

    def send_data(self):
        self._queue += self._pop_data_from_oldest_file(Postman.MAX_STATS_FROM_FILE)

        not_sent_data_queue = []
        server_unreachable = False
        while self._queue:
            data = self._queue.pop()
            if not server_unreachable:
                code, error = self._post_data("api/stats/", data)
                if isinstance(error, requests.Timeout):
                    log.error("Server is not reachable. Omitting future POSTs from this send_data call "
                              "and storing data locally")
                    server_unreachable = True
            if server_unreachable or code != 201:
                not_sent_data_queue.append(data)

        # save timeouted stats to file
        if not_sent_data_queue:
            self.append_write(not_sent_data_queue)

    def safe_queue_append(self, data):
        self._lock.acquire()
        self._queue.append(data)
        self._lock.release()

    def _post_data(self, url, data):
        log.debug("Data to be send: {}".format(data))

        error = None
        retries = Postman.MAX_RETRIES
        while retries > 0:
            retries -= 1
            try:
                ds_indicator.safe_reset(self._post_data.__qualname__, DeviceStatus.HIGH_SEVERITY_MALFUNCTION)
                response = requests.post(self.server_url+url, json=data, headers=Postman.HEADERS, timeout=5)
                ds_indicator.safe_reset(self._post_data.__qualname__, DeviceStatus.LOW_SEVERITY_MALFUNCTION)
                if response.status_code != 201:
                    log.error("Server respond with code: {}".format(response.status_code))
                    log.debug("Server error message: {}".format(response.text))
                    ds_indicator.safe_indicate(self._post_data.__qualname__, DeviceStatus.HIGH_SEVERITY_MALFUNCTION)
                else:
                    log.debug("Data sent successfully!")

                return response.status_code, None

            except requests.RequestException as e:
                error = e
                log.warning("Request exception occurred. Trying {} more times. Exception: {}"
                            .format(retries+1, e))
                ds_indicator.safe_indicate(self._post_data.__qualname__, DeviceStatus.LOW_SEVERITY_MALFUNCTION)
        return None, error
