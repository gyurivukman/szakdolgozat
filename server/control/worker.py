import logging
import time

from threading import Thread
from queue import Empty

from .message import *
from .abstract import Singleton
from .database import DatabaseAccess

from model.task import Task


moduleLogger = logging.getLogger(__name__)


class WorkerPool(metaclass=Singleton):

    def __init__(self):
        self.__databaseAccess = DatabaseAccess()
        self.__logger = moduleLogger.getChild("WorkerPool")
        self.__instantWorker = InstantWorker(self.__databaseAccess)
        self.__instantWorkerThread = Thread(target=self.__instantWorker.start)

        self.__longWorker = LongTaskWorker(self.__databaseAccess)
        self.__longWorkerThread = Thread(target=self.__longWorker.start)

    def start(self):
        self.__instantWorkerThread.start()
        self.__longWorkerThread.start()

    def stop(self):
        self.__logger.debug("Stopping")
        self.__instantWorker.stop()
        self.__instantWorkerThread.join()
        self.__longWorker.stop()
        self.__longWorkerThread.join()

        self.__databaseAccess.close()


class Worker():

    def __init__(self, databaseAccess):
        self._databaseAccess = databaseAccess
        self._shouldRun = True
        self._logger = self._getLogger()
        self._messageDispatcher = MessageDispatcher()
        self._currentTask = None
        self._handlerMap = None

    def start(self):
        self._handlerMap = self._createHandlerMap()
        while self._shouldRun:
            try:
                if not self._currentTask:
                    self._currentTask = self._getNewTask()
                self._work()
                self._finishTask()
            except Empty:
                time.sleep(1.0) # TODO Busy waiting is bad mkay?

    def _getLogger(self):
        raise NotImplementedError("Derived class must implement method '_getLogger'! It should return a logger.")

    def _work(self):
        raise NotImplementedError("Derived class must implement method '_work()' !")

    def _getNewTask(self):
        raise NotImplementedError("Derived class must implement method '_getNewTask' !")

    def _finishTask(self):
        raise NotImplementedError("Derived class must implement method '_finishTask' !")

    def stop(self):
        self._shouldRun = False


class LongTaskWorker(Worker):

    def _createHandlerMap(self):
        return {
            MessageTypes.UPLOAD_FILE: UploadFileHandler(self._databaseAccess),
            MessageTypes.DOWNLOAD_FILE: DownloadFileHandler(self._databaseAccess)
        }

    def _work(self):
        handler = self._handlerMap[self._currentTask.taskType]
        handler.setTask(self._currentTask)
        handler.handle()
        self._currentTask = None

    def _getLogger(self):
        return moduleLogger.getChild("LongTaskWorker")

    def _getNewTask(self):
        message = self._messageDispatcher.incoming_task_queue.get_nowait()
        return Task(taskType=message.header.messageType, stale=False, state="INIT", uuid=message.header.uuid, data=message.data)

    def _finishTask(self):
        self._messageDispatcher.incoming_task_queue.task_done()


class InstantWorker(Worker):

    def _createHandlerMap(self):
        return {
            MessageTypes.GET_ACCOUNT_LIST: GetAccountsListHandler(self._databaseAccess),
            MessageTypes.SET_ACCOUNT_LIST: SetAccountListHandler(self._databaseAccess),
            MessageTypes.SYNC_FILES: GetFileListHandler(self._databaseAccess),
            MessageTypes.GET_WORKSPACE: GetWorkspaceHandler(self._databaseAccess),
            MessageTypes.DELETE_FILE: DeleteFileHandler(self._databaseAccess),
            MessageTypes.MOVE_FILE: MoveFileHandler(self._databaseAccess)
        }

    def _work(self):
        handler = self._handlerMap[self._currentTask.taskType]
        handler.setTask(self._currentTask)
        handler.handle()
        self._currentTask = None

    def _getNewTask(self):
        message = self._messageDispatcher.incoming_instant_task_queue.get_nowait()
        return Task(taskType=message.header.messageType, stale=False, state="INIT", uuid=message.header.uuid, data=message.data)

    def _getLogger(self):
        return moduleLogger.getChild("InstantWorker")

    def _finishTask(self):
        self._messageDispatcher.incoming_instant_task_queue.task_done()
