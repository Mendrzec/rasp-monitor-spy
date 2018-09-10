from spy.settings import DATE_FORMAT, LOG_LOGGER_NAME
from spy.utils import DeviceStatusIndicator, DeviceStatus
from threading import Lock

import logging
import hashlib
import psutil
import socket
import time


STAT_TEMPLATE = {
    'card_id': "",
    'machine': {
        'hash': "",
        'name': "",
        'ip': ""
    },
    'events': []
}

log = logging.getLogger(LOG_LOGGER_NAME)
ds_indicator = DeviceStatusIndicator()


class Machine:
    __instance = None
    __init_complete = False

    DEFAULT_INTERFACE = "eth0"

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, interface_name=DEFAULT_INTERFACE):
        if not Machine.__init_complete:
            self.name = Machine._get_host_name()
            ip = Machine._get_host_ip(interface_name)
            self.ip = ip if ip else "NO_IP"
            self.hash = self._create_hash()
            if self.ip != "NO_IP":
                Machine.__init_complete = True

    @staticmethod
    def _get_host_name():
        hostname = socket.gethostname()
        return hostname if hostname else "UNKNOWN_HOSTNAME"

    @staticmethod
    def _get_host_ip(interface_name):
        interfaces = psutil.net_if_addrs()

        interface = interfaces.get(interface_name, None)
        ip = Machine._get_interface_ip(interface)
        if ip:
            return ip

        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ds_indicator.safe_reset(Machine._get_host_ip.__qualname__, DeviceStatus.LOW_SEVERITY_MALFUNCTION)
        except OSError as e:
            log.warning("Could not determine ip by pinging 8.8.8.8. Exception: {}".format(e))
            ds_indicator.safe_indicate(Machine._get_host_ip.__qualname__, DeviceStatus.LOW_SEVERITY_MALFUNCTION)
            return None

        ip = s.getsockname()[0]
        for interface in interfaces.values():
            filtered = filter(lambda _snic: _snic.family == socket.AF_INET and _snic.address == ip, interface)
            if next(filtered, None):
                ip = Machine._get_interface_ip(interface)
                if ip:
                    return ip

        return None

    @staticmethod
    def _get_interface_ip(interface):
        ip = None
        if interface:
            for snic in interface:
                if snic.family == socket.AF_INET:
                    ip = snic.address
            log.debug("Host ip is: {}".format(ip))
            if ip:
                return ip
        return None

    def _create_hash(self):
        return hashlib.sha1(bytes(self.name, 'utf-8')).hexdigest()

    def to_dict(self):
        return {
            'name': self.name,
            'ip': self.ip,
            'hash': self.hash
        }


class Event:
    PRECISION = 2  # digits after decimal point

    TYPE_MACHINE_ON_OFF = 'MACHINE_ON_OFF'
    TYPE_CYCLES_COUNT = 'CYCLES_COUNT'
    TYPE_CYCLES_COUNT_LATCH = 'CYCLES_COUNT_LATCH'
    TYPE_CYCLES_PER_MINUTE = 'CYCLES_PER_MINUTE'
    TYPE_CYCLES_PER_MINUTE_LATCH = 'CYCLES_PER_MINUTE_LATCH'

    def __init__(self, type_, value):
        self.type = type_
        self.value = str(round(value, Event.PRECISION))
        self.timestamp = time.strftime(DATE_FORMAT, time.gmtime())

    def to_dict(self):
        return {
            'type': self.type,
            'value': self.value,
            'timestamp': self.timestamp
        }


class Stat:
    __instance = None

    CARD_ID_NONE = "NO_CARD"

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, card_id=CARD_ID_NONE):
        self.card_id = card_id
        self.events = []
        self._lock = Lock()

    def add_event(self, type_, value):
        self._lock.acquire()
        self.events.append(Event(type_, value))
        self._lock.release()

    def dump_and_clean(self):
        self._lock.acquire()
        stat = {}
        stat['card_id'] = self.card_id
        stat['events'] = [event.to_dict() for event in self.events]
        stat['machine'] = Machine().to_dict()
        stat['timestamp'] = time.strftime(DATE_FORMAT, time.gmtime())
        self.events.clear()
        self._lock.release()
        return stat
