import logging
import time

from threading import Thread
from queue import Empty

from .message import MessageDispatcher, MessageTypes
from .message import GetAccountsListHandler, SetAccountListHandler
from .abstract import Singleton
from .database import DatabaseAccess

from model.task import Task

module_logger = logging.getLogger(__name__)


class WorkerPool(metaclass=Singleton):

    def __init__(self):
        self._logger = logging.getLogger(__name__).getChild("WorkerPool")
        self._instant_worker = InstantWorker()
        self._instant_worker_thread = Thread(target=self._instant_worker.start)

    def start(self):
        self._instant_worker_thread.start()

    def stop(self):
        self._logger.debug("Stopping")
        self._instant_worker.stop()
        self._instant_worker_thread.join()


class Worker():

    def __init__(self):
        self._shouldRun = True
        self._logger = self._getLogger()
        self._messageDispatcher = MessageDispatcher()
        self._currentTask = None
        self._handlerMap = None
        self._databaseAccess = None

    def start(self):
        self._databaseAccess = DatabaseAccess()
        self._handlerMap = self._createHandlerMap()
        while self._shouldRun:
            try:
                if not self._currentTask:
                    self._currentTask = self._getNewTask()
                self._work()
            except Empty:
                time.sleep(1.0)
        self._databaseAccess.close()

    def _getLogger(self):
        raise NotImplementedError("Derived class must implement method '_getLogger'! It should return a logger.")

    def _work(self):
        raise NotImplementedError("Derived class must implement method '_work()' !")

    def _getNewTask(self):
        raise NotImplementedError("Derived class must implement method '_getNewTask' !")

    def stop(self):
        self._shouldRun = False


class InstantWorker(Worker):

    def _createHandlerMap(self):
        return {
            MessageTypes.GET_ACCOUNT_LIST: GetAccountsListHandler(self._databaseAccess),
            MessageTypes.SET_ACCOUNT_LIST: SetAccountListHandler(self._databaseAccess)
        }

    def _work(self):
        handler = self._handlerMap[self._currentTask.taskType]
        handler.setTask(self._currentTask)
        handler.handle()
        self._currentTask = None
        self._messageDispatcher.incoming_instant_task_queue.task_done()

    def _getNewTask(self):
        message = self._messageDispatcher.incoming_instant_task_queue.get_nowait()
        return Task(taskType=message.header.messageType, stale=False, state="INIT", uuid=message.header.uuid, data=message.data)

    def _getLogger(self):
        return module_logger.getChild("InstantWorker")
