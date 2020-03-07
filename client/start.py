import logging

from threading import Thread
from sys import stdout
from time import sleep

from services.taskhandler import TaskMaster


logging.basicConfig(
    format='%(asctime)s [CLIENT] %(name)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=stdout
)
logger = logging.getLogger()


if __name__ == "__main__":
    try:
        taskMaster = TaskMaster()
        taskMasterThread = Thread(target=taskMaster.run)
        taskMasterThread.start()
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt received, stopping client. Please wait...")
        taskMaster.stop()
        logger.info("Taskmaster signaled to stop")
    taskMasterThread.join()
    logger.info("Taskmaster joined")
