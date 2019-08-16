import signal
import threading

# absolute imports
# import app.app_threads
# from app.logger import Logger
# from app.apic import APIC

# relative imports
from .. import app
from ..logger import Logger
from .apic import APIC

exit = threading.Event() # condition in all looping threads, exit when set
lock = threading.Lock() # global lock for the app; does not impact performance due to Cython GIL
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

def clear_log():
    with open("aurora.log", "w"):
        pass

def main():
    signal.signal(signal.SIGINT, handler)

    clear_log()
    logger = Logger.get_logger()
    logger.info("Starting app")

    logger.info("Starting APIC cookie thread")
    apic_thread = app.app_threads.APICThread(exit, lock)
    apic_thread.start()
    logger.info("APIC cookie thread started successfully")

    logger.info("Starting Kafka consumer thread")
    epg_thread = app.app_threads.ConsumerThread(exit, lock)
    epg_thread.start()
    logger.info("Consumer thread started successfully")

    apic_thread.join()
    epg_thread.join()
    logger.info("App exited succesfully")

if __name__ == '__main__':
    main()
