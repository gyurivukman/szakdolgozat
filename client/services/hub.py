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
    sshStatusChannel = pyqtSignal(object)
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
            self.__logger = logging.getLogger(__name__).getChild("ServiceHub")
            self.__messageArchive = {}

            self.__networkService = None
            self.__networkThread = None
            self.__isNetworkServiceRunning = False
            self.__networkQueue = None

            self.__fileSyncService = None
            self.__isFileSyncServiceRunning = False
            self.__fileSyncThread = None

            self.__sshService = None
            self.__isSshServiceRunning = False
            self.__sshThread = None

            self.initNetworkService()
            self.initFileSyncService()
            self.initSshService()

    def __shutDownThreadedService(self, service, serviceThread):
        service.stop()
        if serviceThread.is_alive():
            serviceThread.join()

    def initNetworkService(self):
        self.__networkQueue = Queue()
        self.__networkService = NetworkClient(self.__networkQueue)
        self.__networkService.messageArrived.connect(self.__onNetworkMessageArrived)
        self.__networkService.connectionStatusChanged.connect(self.__onNetworkConnectionEvent)
        self.__networkThread = Thread(target=self.__networkService.run)

    def initFileSyncService(self):
        self.__fileSyncService = FileSynchronizer()
        self.__fileSyncService.fileEvent.connect(self.__onFileEvent)
        self.__fileSyncThread = Thread(target=self.__fileSyncService.run)

    def initSshService(self):
        self.__sshService = SshClient(self.__fileSyncService)
        self.__sshService.connectionStatusChanged.connect(self.__onSSHConnectionEvent)
        self.__sshThread = Thread(target=self.__sshService.run)

    def startNetworkService(self):
        self.__networkThread.start()
        self.__isNetworkServiceRunning = True
        self.__logger.debug("Network service started")

    def startFileSyncerService(self):
        self.__fileSyncThread.start()
        self.__isFileSyncServiceRunning = True
        self.__logger.debug("File Sync service started")

    def startSshService(self):
        self.__sshThread.start()
        self.__isSshServiceRunning = True
        self.__logger.debug("SSH service started")

    def startAllServices(self):
        self.startNetworkService()
        self.startFileSyncerService()
        self.startSshService()

    def shutdownAllServices(self):
        self.__logger.debug("Stopping all services")

        self.__networkService.stop()
        self.__fileSyncService.stop()
        self.__sshService.stop()

        if self.__fileSyncThread is not None and self.__fileSyncThread.is_alive():
            self.__fileSyncThread.join()
            self.__isFileSyncServiceRunning = False
        if self.__networkThread is not None and self.__networkThread.is_alive():
            self.__networkThread.join()
            self.__isNetworkServiceRunning = False
        if self.__sshThread is not None and self.__sshThread.is_alive():
            self.__sshThread.join()
            self.__isSshServiceRunning = False

        self.__logger.debug("Stopped all services")

    def shutdownNetwork(self):
        self.__shutDownThreadedService(self.__networkService, self.__networkThread)
        self.__networkService = None
        self.__networkThread = None
        self.__isNetworkServiceRunning = False
        self.__logger.debug("Network service stopped")

    def shutdownFileSync(self):
        self.__shutDownThreadedService(self.__fileSyncService, self.__fileSyncThread)
        self.__fileSyncService = None
        self.__fileSyncThread = None
        self.__isFileSyncServiceRunning = False
        self.__logger.debug("File Sync service stopped")

    def shutdownSsh(self):
        self.___shutDownThreadedService(self._sshService, self.__sshThread)
        self.__sshService = None
        self.__sshThread = None
        self.__isSshServiceRunning = False
        self.__logger.debug("SSH service stopped")

    def setNetworkInformation(self, address, port, aesKey):
        self.__networkService.setNetworkInformation(address, port, aesKey)

    def setSSHInformation(self, address, username, password):
        self.__sshService.setSSHInformation(address, username, password)

    def connectToServer(self):
        try:
            self.__networkService.connect()
        except ConnectionError as e:
            self.__logger.debug("Connection Error!")
            self.networkStatusChannel.emit(ConnectionEvent(ConnectionEventTypes.NETWORK_CONNECTION_ERROR, {"message": str(e)}))

    def connectToSSH(self):
        try:
            self.__sshService.connect()
        except ConnectionError as e:
            self.__logger.debug("SSH Connection Error!")
            self.networkStatusChannel.emit(ConnectionEvent(ConnectionEventTypes.NETWORK_CONNECTION_ERROR, {"message": str(e)}))

    def disconnectServer(self):
        self.__networkService.disconnect()

    def disconnectSSH(self):
        self.__sshService.disconnect()

    def sendNetworkMessage(self, message, callBack=None):
        if callBack:
            self.__messageArchive[message.header.uuid] = callBack
        self.__networkService.enqueuMessage(message)

    def isNetworkServiceRunning(self):
        return self.__isNetworkServiceRunning

    def isFileSyncServiceRunning(self):
        return self.__isFileSyncServiceRunning

    def isSshServiceRunning(self):
        return self.__isSshServiceRunning

    def cleanRemoteSSHWorkspace(self):
        self.__sshService.cleanRemoteWorkspace()

    def __onNetworkMessageArrived(self, message):
        if message.header.uuid in self.__messageArchive:
            self.__logger.debug(f"Response: {message.header} {message.data}")
            callBack = self.__messageArchive[message.header.uuid]
            callBack(message.data)
            del self.__messageArchive[message.header.uuid]
        else:
            self.__logger.info(f"Random message: {message.header} {message.data}")

    def __onFileEvent(self, event):
        self.filesChannel.emit(event)

    def __onNetworkConnectionEvent(self, event):
        self.networkStatusChannel.emit(event)

    def __onSSHConnectionEvent(self, event):
        self.sshStatusChannel.emit(event)