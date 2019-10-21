import time
from queue import PriorityQueue

from PyQt5.QtCore import QThread, QObject


class BaseWorkerService(QObject):
    def __init__(self):
        super().__init__()
        self._shouldRun = True

    def start(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'start'. This is the entrypoint for the service.")

    def stop(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'stop'. This is the exit point for the service.")


class TaskBasedWorkerService(BaseWorkerService):
    def __init__(self):
        super().__init__()
        self._currentTask = None
        self._taskQueue = PriorityQueue()


class FileScannerWorkerService(BaseWorkerService):
    def start(self):
        while self._shouldRun:
            print("filescanner working...")
            time.sleep(5)

    def stop(self):
        self._shouldRun = False


class ErrorDisplayService:
    pass


class TaskManager(BaseWorkerService):
    def __init__(self):
        self.__fileScannerThread = QThread()
        self.__fileScannerService = FileScannerWorkerService()
        self.__fileScannerService.moveToThread(self.__fileScannerThread)
        self.__fileScannerThread.started.connect(self.__fileScannerService.start)
    
    def start(self):
        self.__fileScannerThread.start()
    
    def stop(self):
        self.__fileScannerService.stop()
