import sys
import logging

import json

class Logger:
    """Wrapper class around python Logging.Logger"""

    __logger = None

    @classmethod
    def get_logger(cls):
        if cls.__logger == None:
            cls.__logger = Logger.__get_logger()
        return Logger()

    @staticmethod
    def __get_logger():
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # Logging to stdout for ecohub
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG) # TODO change to info?
        logger.addHandler(handler)
        formatter = PigeonFormatter()
        handler.setFormatter(formatter)

        return logger

    def debug(self, msg, data={}):
        data_str = json.dumps(data)
        extra = {'data': data_str}

        return self.__logger.debug(msg, extra=extra)

    def info(self, msg, data={}):
        data_str = json.dumps(data)
        extra = {'data': data_str}

        return self.__logger.info(msg, extra=extra)

    def warning(self, msg, data={}):
        data_str = json.dumps(data)
        extra = {'data': data_str}

        return self.__logger.warning(msg, extra=extra)

    def error(self, msg, data={}):
        data_str = json.dumps(data)
        extra = {'data': data_str}

        return self.__logger.error(msg, extra=extra)

    def critical(self, msg, data={}):
        data_str = json.dumps(data)
        extra = {'data': data_str}

        return self.__logger.info(msg, extra=extra)

    def exception(self, msg, data={}):
        data_str = json.dumps(data)
        extra = {'data': data_str}

        return self.__logger.exception(msg, extra=extra)

    def log(self, level, msg, data={}):
        data_str = json.dumps(data)
        extra = {'data': data_str}

        return self.__logger.log(level, msg, extra=extra)


class PigeonFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    logging_format = "{{\"status_code\": {0}, \"message\": \"{1}\", \"data\": %(data)s}}"


    FORMATS = {
        logging.ERROR: 400,
        logging.WARNING: 300,
        logging.CRITICAL: 200, # TODO change later
        logging.INFO: 100,
        logging.DEBUG: 100
    }

    def format(self, record):
        # get msg string and escape double quotes
        msg_formatter = logging.Formatter("%(msg)s")
        escaped_quotes = msg_formatter.format(record).replace('\"','\\\"')

        # insert status snow and escaped msg into format string
        status_code = self.FORMATS.get(record.levelno, 404)
        json_msg = self.logging_format.format(status_code, escaped_quotes)

        # format 'data' field into final output
        output_formatter = logging.Formatter(json_msg)
        return output_formatter.format(record)
