from spy.settings import LOG_CONFIG, LOG_LOGGER_NAME

import json
import logging.config
import os


logging.config.dictConfig(LOG_CONFIG)
log = logging.getLogger(LOG_LOGGER_NAME)


class PostmanFileHelper:
    MAX_FILE_SIZE = 512 * 1024

    def __init__(self, base_file_path):
        self.base_file_path = base_file_path

        self.base_file_name, self.base_file_extension = os.path.splitext(os.path.basename(self.base_file_path))

        files_dir = os.path.dirname(self.base_file_path)
        self.dir = files_dir if files_dir != "" else os.path.curdir

    def get_existing_files(self):
        existing_files_dict = {}
        existing_files = []
        for file in os.listdir(self.dir):
            if file.startswith(self.base_file_name) and file.endswith(self.base_file_extension):
                existing_files.append(file)

        for file in existing_files:
            file_without_extension = file.replace(self.base_file_extension, "")
            index = file_without_extension.rsplit("_", maxsplit=1)[1]
            existing_files_dict[index] = file

        log.debug("Existing files found: {}".format(existing_files))
        return existing_files_dict

    def append_write(self, data):
        log.debug("Data to be saved: {}".format(data))
        existing_files = self.get_existing_files()

        # CREATE NEW if no previous file
        if not existing_files:
            fresh_file_path = self._regenerate_file_path(str(1))
            log.debug("Not found any previous files. Creating new one: '{}'".format(fresh_file_path))
            self._append_write_to_file(data, fresh_file_path)
            return

        # APPEND if remaining space in file is sufficient to append data
        latest_file_index = sorted(existing_files)[-1]
        latest_file_path = self._regenerate_file_path(latest_file_index)
        json_data_size = len(json.dumps(data, indent=2))
        if os.path.getsize(latest_file_path) + json_data_size < PostmanFileHelper.MAX_FILE_SIZE:
            existent_data = self.safe_read_json_decode(latest_file_path)
            self._append_write_to_file(data, latest_file_path, previous_data=existent_data)
            return

        # CREATE NEW if not enough space
        fresh_file_path = self._regenerate_file_path(str(int(latest_file_index)+1))
        log.debug("File '{}' is full, creating new one '{}'".format(latest_file_path, fresh_file_path))
        self._append_write_to_file(data, fresh_file_path)

    def _pop_data_from_oldest_file(self, count):
        existing_files = self.get_existing_files()
        if not existing_files:
            return []

        oldest_file_index = sorted(existing_files)[0]
        oldest_file_path = self._regenerate_file_path(oldest_file_index)
        not_sent_data = self.safe_read_json_decode(oldest_file_path)
        if not isinstance(not_sent_data, list):
            log.error("Previous data from file '{}' are not a list. Cannot add to send queue!"
                      .format(oldest_file_path))
            # TODO: Handle reading from next files if opened one is corrupted
            return []

        # pop some stats and save rest
        result = not_sent_data[-count:]
        del not_sent_data[-count:]
        log.debug("{} elements read from stats not sent file {}".format(len(result), oldest_file_path))

        if not_sent_data:
            self.safe_write(oldest_file_path, json.dumps(not_sent_data, indent=2))
        elif os.path.exists(oldest_file_path):
            log.info("Popped all data from file '{}'. Removing it...".format(oldest_file_path))
            os.remove(oldest_file_path)

        return result

    def _append_write_to_file(self, data, file_path, previous_data=None):
        data_to_write = previous_data if previous_data is not None else []
        if not isinstance(data_to_write, list):
            log.error("Previous data are not a list, cannot append!")
            return

        if isinstance(data, list):
            data_to_write += data
        else:
            data_to_write.append(data)
        self.safe_write(file_path, json.dumps(data_to_write, indent=2))

    def _regenerate_file_path(self, index: str):
        return self.dir + "/" + self.base_file_name + "_" + index + self.base_file_extension

    @staticmethod
    def safe_write(file_name, data: str):
        file = None
        try:
            file = open(file_name, mode="w", newline="\n")
            file.write(data)
        except IOError:
            log.error("Could not open file: '{}'. Exception traceback: ".format(file_name), exc_info=True)

        if file is not None:
            file.close()

    @staticmethod
    def safe_read_json_decode(file_name):
        json_file = None
        json_data = None
        try:
            json_file = open(file_name, mode="r", newline="\n")
            json_data = json.load(json_file)
        except IOError:
            log.error("Could not open file: '{}'. Exception traceback: ".format(file_name), exc_info=True)
        except json.JSONDecodeError:
            log.error("Could not parse data from file: '{}'. Exception traceback:".format(file_name), exc_info=True)

        if json_file is not None:
            json_file.close()
        if json_data is not None:
            return json_data

        return None
