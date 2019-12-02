import signal
import threading

# absolute imports
# import consumer.app_threads
# from consumer.logger import Logger
# from consumer.apic import APIC

# relative imports
from .. import consumer
from ..logger import Logger

exit = threading.Event() # condition in all looping threads, exit when set
lock = threading.Lock() # global lock for the consumer; does not impact performance due to Python GIL
# necessary for any shared resources between threads
# currently used to prevent two threads from getting different APIC sessions
# REVIEW do not believe it is necessary for get_logger()

def handler(signum, frame):
    logger = Logger.get_logger()
    logger.info("Received SIGINT. Attempting shutdown")
    exit.set()

# def loop():
#     """Prevent main thread from blocking in low-level function call,
#     e.g. C level `pthread_join()`
#     Allow signals to reach python signal handler, pre python-3.3
#     """
#     while not exit.is_set():
#         print("Main thread ")
#         exit.wait(300)


def main():
    signal.signal(signal.SIGINT, handler)

    logger = Logger.get_logger()
    logger.info("Starting consumer")

    logger.info("Starting APIC cookie thread")
    apic_thread = consumer.app_threads.APICThread(exit, lock)
    apic_thread.start()
    logger.info("APIC cookie thread started successfully")

    logger.info("Starting Kafka consumer thread")
    epg_thread = consumer.app_threads.ConsumerThread(exit, lock)
    epg_thread.start()
    logger.info("Consumer thread started successfully")

    apic_thread.join()
    epg_thread.join()
    logger.critical("App exited succesfully") #TODO change level

if __name__ == '__main__':
    main()
