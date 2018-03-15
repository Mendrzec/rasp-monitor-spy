from spy.settings import DATE_FORMAT, LOG_LOGGER_NAME
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


class Machine:
    __instance = None
    __init_done = False

    DEFAULT_INTERFACE = "eth0"

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, interface_name=DEFAULT_INTERFACE):
        if not Machine.__init_done:
            Machine.__init_done = True

            self.name = Machine._get_host_name()
            ip, mac = Machine._get_host_ip_and_mac(interface_name)
            self.ip = ip if ip else "NO_IP"
            self.mac = mac if mac else "NO_MAC"
            self.hash = self._create_hash()

    @staticmethod
    def _get_host_name():
        hostname = socket.gethostname()
        return hostname if hostname else "UNKNOWN_HOSTNAME"

    @staticmethod
    def _get_host_ip_and_mac(interface_name):
        interfaces = psutil.net_if_addrs()

        interface = interfaces.get(interface_name, None)
        ip, mac = Machine._get_interface_ip_and_mac(interface)
        if ip and mac:
            return ip, mac

        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        for interface in interfaces.values():
            filtered = filter(lambda _snic: _snic.family == socket.AF_INET and _snic.address == ip, interface)
            if next(filtered, None):
                ip, mac = Machine._get_interface_ip_and_mac(interface)
                if ip and mac:
                    return ip, mac

        return None, None

    @staticmethod
    def _get_interface_ip_and_mac(interface):
        mac = None
        ip = None
        if interface:
            for snic in interface:
                if snic.family == psutil.AF_LINK:
                    mac = snic.address
                elif snic.family == socket.AF_INET:
                    ip = snic.address

            log.debug("Host ip and mac is: {}, {}".format(ip, mac))
            if ip and mac:
                return ip, mac
        return None, None

    def _create_hash(self):
        sequence = self.mac + self.name
        return hashlib.sha1(bytes(sequence, 'utf-8')).hexdigest()

    def to_dict(self):
        return {
            'name': self.name,
            'ip': self.ip,
            'hash': self.hash
        }


class Event:
    PRECISION = 2  # digits after decimal point

    TYPE_MACHINE_ON_OFF = 'MACHINE_ON_OFF'
    TYPE_CARD_IN_OUT = 'CARD_IN_OUT'
    TYPE_CYCLES_COUNT = 'CYCLES_COUNT'
    TYPE_CYCLES_COUNT_LATCH = 'CYCLES_COUNT_LATCH'
    TYPE_CYCLES_PER_MINUTE = 'CYCLES_PER_MINUTE'
    TYPE_CYCLES_PER_MINUTE_LATCH = 'CYCLES_PER_MINUTE_LATCH'

    VALUE_CARD_IN = 1
    VALUE_CARD_OUT = 0

    def __init__(self, type_, value):
        self.type = type_
        self.value = str(round(value, Event.PRECISION))
        self.timestamp = time.strftime(DATE_FORMAT)

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
        self.machine = Machine()
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
        stat['machine'] = self.machine.to_dict()
        self.events.clear()
        self._lock.release()
        return stat
