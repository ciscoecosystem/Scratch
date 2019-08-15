import os
import yaml
import logging
import logging.handlers


class Logger(object):
    __logger = None

    @classmethod
    def get_logger(cls):
        if cls.__logger == None:
            cls.config = Logger.load_config()
            cls.__logger = Logger.__get_logger(cls.config)
        return cls.__logger


    @staticmethod
    def load_config():
        """
        loads the configuration from yaml file
        """
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)

    
    @staticmethod
    def __get_logger(config):
        log_level = config['log_level']
        backup_count = config['backup_count']
        
        setattr(logging, 'level', log_level.upper())
        logging.basicConfig(level=logging.level)
        logger = logging.getLogger(__name__)
        # logger.setLevel(logging.DEBUG)
        
        log_dirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        if not os.path.exists(log_dirpath):
            os.makedirs(log_dirpath)

        # create a file handler
        # handler = logging.handlers.RotatingFileHandler(filename=log_filename, maxBytes=1000000, backupCount=backup_count)
        handler = logging.handlers.TimedRotatingFileHandler(filename=os.path.join(log_dirpath, 'aurora.log'), when='midnight', backupCount=backup_count)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(handler)

        return logger
