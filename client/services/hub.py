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
            self._isNetworkServiceRunning = False
            self._networkQueue = None

            self._fileSyncService = None
            self._isFileSyncServiceRunning = False
            self._fileSyncThread = None

            self._sshService = None
            self._isSshServiceRunning = False
            self._sshThread = None

            self.initNetworkService()
            self.initFileSyncService()
            self.initSshService()

    def _shutDownThreadedService(self, service, serviceThread):
        service.stop()
        if serviceThread.is_alive():
            serviceThread.join()

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
        self._sshThread = Thread(target=self._sshService.run)

    def startNetworkService(self):
        self._networkThread.start()
        self._isNetworkServiceRunning = True
        self._logger.debug("Network service started")

    def startFileSyncerService(self):
        self._fileSyncThread.start()
        self._isFileSyncServiceRunning = True
        self._logger.debug("File Sync service started")

    def startSshService(self):
        self._sshThread.start()
        self._isSshServiceRunning = True
        self._logger.debug("SSH service started")

    def startAllServices(self):
        self.startNetworkService()
        self.startFileSyncerService()
        self.startSshService()

    def shutdownAllServices(self):
        self._logger.debug("Stopping all services")

        self._networkService.stop()
        self._fileSyncService.stop()
        self._sshService.stop()

        if self._fileSyncThread is not None and self._fileSyncThread.is_alive():
            self._logger.debug("Joining FILESYNC")
            self._fileSyncThread.join()
            self._isFileSyncServiceRunning = False
            self._logger.debug("Joined FILESYNC")
        if self._networkThread is not None and self._networkThread.is_alive():
            self._logger.debug("Joining NETWORK")
            self._networkThread.join()
            self._isNetworkServiceRunning = False
            self._logger.debug("Joined NETWORK")
        if self._sshThread is not None and self._sshThread.is_alive():
            self._logger.debug("Joining SSH")
            self._sshThread.join()
            self._isSshServiceRunning = False
            self._logger.debug("Joined SSH")

        self._logger.debug("Stopped all services")

    def shutdownNetwork(self):
        self._shutDownThreadedService(self._networkService, self._networkThread)
        self._networkService = None
        self._networkThread = None
        self._isNetworkServiceRunning = False
        self._logger.debug("Network service stopped")

    def shutdownFileSync(self):
        self._shutDownThreadedService(self._fileSyncService, self._fileSyncThread)
        self._fileSyncService = None
        self._fileSyncThread = None
        self._isFileSyncServiceRunning = False
        self._logger.debug("File Sync service stopped")

    def shutdownSsh(self):
        self._shutDownThreadedService(self._sshService, self._sshThread)
        self._sshService = None
        self._sshThread = None
        self._isSshServiceRunning = False
        self._logger.debug("SSH service stopped")

    def setNetworkInformation(self, address, port, aesKey):
        self._networkService.setNetworkInformation(address, port, aesKey)

    def setSSHInformation(self, address, username, password):
        self._sshService.setSSHInformation(address, username, password)

    def connectToServer(self):
        try:
            self._networkService.connect()
        except ConnectionError as e:
            self._logger.debug("Connection Error!")
            self.networkStatusChannel.emit(ConnectionEvent(ConnectionEventTypes.CONNECTION_ERROR, {"message": str(e)}))

    def connectToSSH(self):
        try:
            self._sshService.connect()
        except ConnectionError as e:
            self._logger.debug("SSH Connection Error!")
            self.networkStatusChannel.emit(ConnectionEvent(ConnectionEventTypes.CONNECTION_ERROR, {"message": str(e)}))

    def disconnectServer(self):
        self._networkService.disconnect()

    def disconnectSSH(self):
        self._sshService.disconnect()

    def sendNetworkMessage(self, message, callBack=None):
        if callBack:
            self._messageArchive[message.header.uuid] = callBack
        self._networkService.enqueuMessage(message)

    def isNetworkServiceRunning(self):
        return self._isNetworkServiceRunning

    def isFileSyncServiceRunning(self):
        return self._isFileSyncServiceRunning

    def isSshServiceRunning(self):
        return self._isSshServiceRunning

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
