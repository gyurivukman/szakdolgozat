import logging

from enum import IntEnum
from queue import Queue


class MessageTypes(IntEnum):
    GET_ACCOUNT_LIST = 0


class MessageDispatcher(object):
    __instance = None

    def __init__(self):
        if MessageDispatcher.__instance is not None:
            raise Exception("This class is a singleton! use MessageDispatcher.getInstance() instead!")
        else:
            MessageDispatcher.__instance = self

            self.incoming_instant_task_queue = Queue()
            self.incoming_task_queue = Queue()
            self.outgoing_task_queue = Queue()

            self._logger = logging.getLogger(__name__).getChild("MessageDispatcher")

    @staticmethod
    def getInstance():
        if MessageDispatcher.__instance is None:
            MessageDispatcher()
        return MessageDispatcher.__instance


class WorkerPool(object):
    __instance = None

    def __init__(self):
        if WorkerPool.__instance is not None:
            raise Exception("This class is a singleton! use WorkerPool.getInstance() instead!")
        else:
            WorkerPool.__instance = self

            self._logger = logging.getLogger(__name__).getChild("WorkerPool")

            self._instant_worker = None #TODO
            self._instant_worker_thread =None #TODO

    @staticmethod
    def getInstance():
        if WorkerPool.__instance is None:
            WorkerPool()
        return WorkerPool.__instance

    def start(self):
        self._instant_worker_thread.start()

    def stop(self):
        self._instant_worker.stop()
        self._instant_worker_thread.join()
