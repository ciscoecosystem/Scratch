import os
import logging


class Logger(object):
    __logger = None

    @classmethod
    def get_logger(cls):
        if cls.__logger == None:
            cls.__logger = Logger.__get_logger()
        return cls.__logger


    @staticmethod
    def __get_logger():
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # create a file handler
        handler = logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aurora.log'))
        handler.setLevel(logging.DEBUG)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(handler)

        return logger
