import logging
import time

from .message import MessageDispatcher

module_logger = logging.getLogger(__name__)


class Worker():

    def __init__(self):
        self._messageDispatcher = MessageDispatcher.getInstance()
        self._shouldRun = True
        self._logger = module_logger.getChild(__class__)
        self._currentTask = None

    def start(self):
        while self._shouldRun:
            self._work()

    def _work(self):
        raise NotImplementedError("Derived class must implement method '_work()' !")

    def stop(self):
        self._shouldRun = False


class InstantWorker(self):

    def _work(self):
        pass
