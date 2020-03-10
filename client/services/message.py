import logging
import time

from multiprocessing import Queue
from threading import Thread
from queue import Empty

from .network import NetworkClient, SshClient
from .files import FileSynchronizer

from PyQt5.QtCore import QObject, pyqtSignal


class MessageDispatcher(QObject):
    __instance = None
    fileStatusChanged = pyqtSignal(object)

    @staticmethod
    def getInstance():
        if MessageDispatcher.__instance is None:
            MessageDispatcher()
        return MessageDispatcher.__instance

    def __init__(self):
        if MessageDispatcher.__instance is not None:
            raise Exception("This class is a singleton! use TaskManager.getInstance() instead!")
        else:
            super().__init__()
            MessageDispatcher.__instance = self
            self._logger = logging.getLogger(__name__).getChild("MessageDispatcher")

            self._networkService = None
            self._networkThread = None

            self._fileSyncService = None
            self._fileSyncThread = None

            self._sshService = None
            self._sshThread = None

            self.initNetworkService()
            self.initFileSyncService()
            self.initSshService()

    def initNetworkService(self):
        self._networkService = NetworkClient()
        self._networkService.messageArrived.connect(self._onNetworkMessageArrived)
        self._networkThread = Thread(target=self._networkService.run)

    def initFileSyncService(self):
        self._fileSyncService = FileSynchronizer()
        self._fileSyncService.fileEvent.connect(self._onFileEvent)
        self._fileSyncThread = Thread(target=self._fileSyncService.run)

    def initSshService(self):
        self._sshService = SshClient(self._fileSyncService)
        # self._sshService.messageArrived.connect(self._onNetworkMessageArrived)
        self._sshThread = Thread(target=self._sshService.run)

    def startNetworkService(self):
        self._networkThread.start()

    def startFileSyncerService(self):
        self._fileSyncThread.start()

    def startSshService(self):
        self._sshThread.start()

    def startAllServices(self):
        self._networkThread.start()
        self._fileSyncThread.start()
        self._sshThread.start()

    def shutdownAllServices(self):
        self._logger.debug("Stopping all services")

        self._networkService.stop()
        self._fileSyncService.stop()
        self._sshService.stop()

        self._fileSyncThread.join()
        self._networkThread.join()
        self._sshThread.join()

        self._logger.debug("Stopped all services")

    def _shutDownThreadedService(self, service, thread):
        service.stop()
        thread.join()

    def shutdownNetwork(self):
        self._shutDownThreadedService(self._networkService, self._networkThread)
        self._networkService = None
        self._networkThread = None

    def shutdownFileSync(self):
        self._shutDownThreadedService(self._fileSyncService, self._fileSyncThread)
        self._fileSyncService = None
        self._fileSyncThread = None

    def _onNetworkMessageArrived(self, message):
        self.fileStatusChanged.emit(message)

    def _onFileEvent(self, event):
        self.fileStatusChanged.emit(event)
