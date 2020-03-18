import logging
import time

from threading import Thread
from queue import Empty

# TODO temporary imports
import string
import random
from uuid import uuid4

from .message import MessageDispatcher
from model.message import NetworkMessage

module_logger = logging.getLogger(__name__)


class WorkerPool(object):
    __instance = None

    def __init__(self):
        if WorkerPool.__instance is not None:
            raise Exception("This class is a singleton! use WorkerPool.getInstance() instead!")
        else:
            WorkerPool.__instance = self

            self._logger = logging.getLogger(__name__).getChild("WorkerPool")

            self._instant_worker = InstantWorker()
            self._instant_worker_thread = Thread(target=self._instant_worker.start)

    @staticmethod
    def getInstance():
        if WorkerPool.__instance is None:
            WorkerPool()
        return WorkerPool.__instance

    def start(self):
        self._instant_worker_thread.start()

    def stop(self):
        self._logger.debug("Stopping")
        self._instant_worker.stop()
        self._instant_worker_thread.join()


class Worker():

    def __init__(self):
        self._messageDispatcher = MessageDispatcher.getInstance()
        self._shouldRun = True
        self._logger = module_logger.getChild(str(self.__class__))
        self._currentTask = None

    def start(self):
        while self._shouldRun:
            try:
                if not self._currentTask:
                    self._currentTask = self._getNewTask()
                self._work()
            except Empty:
                time.sleep(1.0)

    def _work(self):
        raise NotImplementedError("Derived class must implement method '_work()' !")

    def _getNewTask(self):
        raise NotImplementedError("Derived class must implement method '_getNewTask' !")

    def stop(self):
        self._shouldRun = False


class InstantWorker(Worker):

    def _work(self):
        self._logger.debug(f"{self._currentTask.header.uuid} {self._currentTask.data}")
        self._currentTask = None
        self._messageDispatcher.incoming_instant_task_queue.task_done()
        self._messageDispatcher.outgoing_task_queue.put(self._generateRandomResponse())

    def _getNewTask(self):
        return self._messageDispatcher.incoming_instant_task_queue.get_nowait()

    def _generateRandomResponse(self):
        raw = {
            "header": {
                "uuid": uuid4().hex,
            },
            "data": {
                "message": ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(1, 32))),
            }
        }

        return NetworkMessage(raw)
