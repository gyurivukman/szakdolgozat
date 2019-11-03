import time
from queue import PriorityQueue

from PyQt5.QtCore import QThread, QObject

from model.models import Task, TaskPriorities, TaskTypes


class BaseWorkerService(QObject):
    def __init__(self):
        super().__init__()
        self._shouldRun = True

    def start(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'start'. This is the entrypoint for the service.")

    def stop(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'stop'. This is the exit point for the service.")


class TaskBasedServiceWithPriorityQueue():

    def __init__(self):
        self._currentTask = None
        self._taskQueue = PriorityQueue()

    def enqueTask(self, task):
        self._taskQueue.put(task)

    def _handleCurrentTask(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'handleCurrentTask'.")


class ErrorDisplayService:
    pass


class TaskManager(BaseWorkerService):
    __instance = None

    @staticmethod 
    def getInstance():
        if TaskManager.__instance == None:
            TaskManager()
        return TaskManager.__instance

    def __init__(self):
        if TaskManager.__instance != None:
            raise Exception("This class is a singleton! use TaskManager.getInstance() instead!")
        else:
            TaskManager.__instance = self
            super().__init__()
            self.__fileScannerWorker = QThread()
            self.__fileScannerService = FileScannerWorkerService()
            self.__fileScannerService.moveToThread(self.__fileScannerWorker)
            self.__fileScannerWorker.started.connect(self.__fileScannerService.start)

            self.__sshWorker = QThread()
            self.__sshService = SSHService()
            self.__sshService.moveToThread(self.__sshWorker)
            self.__sshWorker.started.connect(self.__sshService.start)

            self.__commsWorker = QThread()
            self.__networkService = NetworkService()
            self.__networkService.moveToThread(self.__commsWorker)
            self.__commsWorker.started.connect(self.__networkService.start)

    def start(self):
        self.__fileScannerWorker.start()
        self.__sshWorker.start()
        self.__commsWorker.start()

    def stop(self):
        self.__fileScannerService.stop()
        self.__sshWorker.stop()
        self.__commsWorker.stop()

    def retrieveAccounts(self, callBack):
        task = Task(TaskPriorities.HIGH, TaskTypes.GET_ACCOUNTS, None, callBack)
        self.__networkService.enqueTask(task)


class NetworkService(BaseWorkerService, TaskBasedServiceWithPriorityQueue):

    def __init__(self):
        super().__init__()
        self.__taskHandlers = self.__createTaskHandlers()

    def __createTaskHandlers(self):
        return {
            TaskTypes.GET_ACCOUNTS: self.__getAccounts
        }

    def start(self):
        while self._shouldRun:
            if not self._currentTask:
                self._currentTask = self._taskQueue.get()
            self._handleCurrentTask()

    def stop(self):
        self._shouldRun = False

    def _handleCurrentTask(self):
        handlerFunction = self.__taskHandlers[self._currentTask.taskType]
        handlerFunction()
        print("Handling some shit....")
        print("calling callback!")
        if self._currentTask.success:
            self._currentTask.success([])
        self._currentTask = None

    def __getAccounts(self):
        print("getting accounts lol")
        time.sleep(2)


class SSHService(BaseWorkerService, TaskBasedServiceWithPriorityQueue):
    def start(self):
        while self._shouldRun:
            print("ssh working...")
            time.sleep(3)

    def stop(self):
        self._shouldRun = False


class FileScannerWorkerService(BaseWorkerService):
    def start(self):
        while self._shouldRun:
            print("filescanner working...")
            time.sleep(3)

    def stop(self):
        self._shouldRun = False
