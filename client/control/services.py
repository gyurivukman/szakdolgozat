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

class ErrorDisplayService:
    pass


class TaskManager(BaseWorkerService):
    def __init__(self):
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


class NetworkService(BaseWorkerService):
    def start(self):
        while self._shouldRun:
            print("networkService working...")
            time.sleep(3)

    def stop(self):
        self._shouldRun = False


class SSHService(BaseWorkerService):
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
