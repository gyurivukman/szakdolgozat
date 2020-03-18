import logging
import time

from threading import Thread
from queue import Queue, Empty

from model.events import ConnectionEvent, ConnectionEventTypes
from .network import NetworkClient, SshClient
from .files import FileSynchronizer


from PyQt5.QtCore import QObject, pyqtSignal


class ServiceHub(QObject):
    __instance = None

    filesChannel = pyqtSignal(object)
    networkStatusChannel = pyqtSignal(object)
    errorChannel = pyqtSignal(object)

    @staticmethod
    def getInstance():
        if ServiceHub.__instance is None:
            ServiceHub()
        return ServiceHub.__instance

    def __init__(self):
        if ServiceHub.__instance is not None:
            raise Exception("This class is a singleton! use ServiceHub.getInstance() instead!")
        else:
            super().__init__()
            ServiceHub.__instance = self
            self._logger = logging.getLogger(__name__).getChild("ServiceHub")
            self._messageArchive = {}

            self._networkService = None
            self._networkThread = None
            self._networkQueue = None

            self._fileSyncService = None
            self._fileSyncThread = None

            self._sshService = None
            self._sshThread = None

            self.initNetworkService()
            self.initFileSyncService()
            self.initSshService()

    def initNetworkService(self):
        self._networkQueue = Queue()
        self._networkService = NetworkClient(self._networkQueue)
        self._networkService.messageArrived.connect(self._onNetworkMessageArrived)
        self._networkService.connectionStatusChanged.connect(self._onConnectionEvent)
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
        self._logger.debug("Network service started")

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

        if self._fileSyncThread is not None and self._fileSyncThread.is_alive():
            self._fileSyncThread.join()
        if self._networkThread is not None and self._fileSyncThread.is_alive():
            self._networkThread.join()
        if self._sshThread is not None and self._sshThread.is_alive():
            self._sshThread.join()

        self._logger.debug("Stopped all services")

    def shutdownNetwork(self):
        self._shutDownThreadedService(self._networkService, self._networkThread)
        self._networkService = None
        self._networkThread = None
        self._logger.debug("Network service stopped")

    def shutdownFileSync(self):
        self._shutDownThreadedService(self._fileSyncService, self._fileSyncThread)
        self._fileSyncService = None
        self._fileSyncThread = None

    def _shutDownThreadedService(self, service, thread):
        service.stop()
        thread.join()

    def setNetworkInformation(self, address, port, aesKey):
        self._networkService.setNetworkInformation(address, port, aesKey)

    def connect(self):
        try:
            self._networkService.connect()
        except ConnectionError as e:
            self._logger.debug("Connection Error!")
            self.networkStatusChannel.emit(ConnectionEvent(ConnectionEventTypes.CONNECTION_ERROR, {"message": str(e)}))

    def disconnect(self):
        self._networkService.disconnect()

    def sendNetworkMessage(self, message, callBack=None):
        if callBack:
            self._messageArchive[message.header.uuid] = callBack
        self._networkService.enqueuMessage(message)

    def _onNetworkMessageArrived(self, message):
        if message.header.uuid in self._messageArchive:
            self._logger.debug(f"Response: {message.header} {message.data}")
            callBack = self._messageArchive[message.header.uuid]
            callBack(message.data)
            del self._messageArchive[message.header.uuid]
        else:
            self._logger.info(f"Random message: {message.header} {message.data}")

    def _onFileEvent(self, event):
        self.filesChannel.emit(event)

    def _onConnectionEvent(self, event):
        self.networkStatusChannel.emit(event)
