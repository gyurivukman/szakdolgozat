import logging
import time

from threading import Thread
from queue import Queue, Empty

from model.networkevents import ConnectionEvent, ConnectionEventTypes
from model.file import FileStatuses, FileStatusEvent, FileEventTypes, FileData
from model.task import FileTask, TaskArchive
from model.message import NetworkMessage, MessageTypes

from .network import NetworkClient, SshClient
from .files import FileSynchronizer


from PyQt5.QtCore import QObject, QSettings, pyqtSignal


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
            self.__sshTaskQueu = None

            self.__fileTaskArchive = TaskArchive()

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
        if self.__fileSyncService:
            self.__fileSyncService.fileTaskChannel.disconnect(self.__onNewFileTask)
            self.__fileSyncService.fileStatusChannel.disconnect(self.__onLocalFileStatusChanged)
        self.__fileSyncService = FileSynchronizer(QSettings().value("syncDir/path"))
        self.__fileSyncService.fileTaskChannel.connect(self.__onNewFileTask)
        self.__fileSyncService.fileStatusChannel.connect(self.__onLocalFileStatusChanged)
        self.__fileSyncThread = Thread(target=self.__fileSyncService.run)

    def initSshService(self):
        self.__sshTaskQueu = Queue()
        self.__sshService = SshClient(self.__fileSyncService, self.__sshTaskQueu)
        self.__sshThread = Thread(target=self.__sshService.run)
        self.__sshService.connectionStatusChanged.connect(self.__onSSHConnectionEvent)
        self.__sshService.taskCompleted.connect(self.__onSSHTaskCompleted)

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

    def shutdownAllServices(self):
        self.__logger.debug("Stopping all services")

        if self.__fileSyncThread is not None and self.__fileSyncThread.is_alive():
            self.__fileSyncService.stop()
            self.__fileSyncThread.join()
            self.__isFileSyncServiceRunning = False
        if self.__networkThread is not None and self.__networkThread.is_alive():
            self.__networkService.stop()
            self.__networkThread.join()
            self.__isNetworkServiceRunning = False
        if self.__sshThread is not None and self.__sshThread.is_alive():
            self.__sshService.stop()
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
        self.__shutDownThreadedService(self.__sshService, self.__sshThread)
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
        self.__networkQueue.put(message)

    def isNetworkServiceRunning(self):
        return self.__isNetworkServiceRunning

    def isFileSyncServiceRunning(self):
        return self.__isFileSyncServiceRunning

    def isSshServiceRunning(self):
        return self.__isSshServiceRunning

    def cleanRemoteSSHWorkspace(self, path):
        self.__sshService.setWorkspace(path)
        self.__sshService.cleanRemoteWorkspace()

    def executeSSHCommand(self, command):
        return self.__sshService.executeCommand(command)

    def syncRemoteAndLocalFiles(self, remoteFiles):
        self.__fileSyncService.syncFileList(remoteFiles)

    def enqueuSSHTask(self, task):
        self.__sshTaskQueu.put(task)

    def __onNetworkMessageArrived(self, message):
        if message.header.messageType == MessageTypes.FILE_STATUS_UPDATE:
            message.data = FileData(**message.data)
            statusChangeEvent = FileStatusEvent(FileEventTypes.STATUS_CHANGED, message.data.fullPath, message.data.status)
            self.filesChannel.emit(statusChangeEvent)
            if message.data.status == FileStatuses.DOWNLOADING_TO_LOCAL:
                task = FileTask(message.header.uuid, FileStatuses.DOWNLOADING_TO_LOCAL, message.data)
                self.__fileTaskArchive.addTask(message.data.fullPath, task)
                self.enqueuSSHTask(task)
        elif message.header.uuid in self.__messageArchive:
            self.__logger.debug(f"Response: {message.header} {message.data}")
            callBack = self.__messageArchive[message.header.uuid]
            callBack(message.data)
            del self.__messageArchive[message.header.uuid]
        else:
            self.__logger.info(f"Unknown message: {message.header} {message.data}")

    def __onNewFileTask(self, task):
        self.__logger.debug(f"New filetask: {task}")
        if task.taskType == FileStatuses.UPLOADING_FROM_LOCAL:
            self.__fileTaskArchive.cancelTask(task.subject.fullPath)
            self.__fileTaskArchive.addTask(task.subject.fullPath, task)

            data = {"fullPath": task.subject.fullPath}
            message = NetworkMessage.Builder(MessageTypes.FILE_TASK_CANCELLED).withData(data).withUUID(task.uuid).build()
            self.sendNetworkMessage(message)
            self.enqueuSSHTask(task)
        elif task.taskType == FileStatuses.DOWNLOADING_FROM_CLOUD:
            data = task.subject.serialize()
            message = NetworkMessage.Builder(MessageTypes.DOWNLOAD_FILE).withData(data).withUUID(task.uuid).build()
            self.sendNetworkMessage(message)
        elif task.taskType == FileStatuses.DELETED:
            self.__fileTaskArchive.cancelTask(task.subject)
            self.__fileTaskArchive.removeTask(task.subject)
            data = {"fullPath": task.subject}
            message = NetworkMessage.Builder(MessageTypes.DELETE_FILE).withData(data).withUUID(task.uuid).build()
            self.sendNetworkMessage(message)
        elif task.taskType == FileStatuses.MOVING:
            self.__fileTaskArchive.cancelTask(task.subject["sourcePath"])
            self.__fileTaskArchive.cancelTask(task.subject["target"].fullPath)
            data = {"source": task.subject["sourcePath"], "target": task.subject["target"].serialize()}
            message = NetworkMessage.Builder(MessageTypes.MOVE_FILE).withData(data).withUUID(task.uuid).build()
            self.sendNetworkMessage(message, task.subject["moveResultCallBack"])

    def __onNetworkConnectionEvent(self, event):
        self.networkStatusChannel.emit(event)

    def __onSSHConnectionEvent(self, event):
        self.sshStatusChannel.emit(event)

    def __onSSHTaskCompleted(self, task):
        if not task.stale:
            if task.taskType == FileStatuses.UPLOADING_FROM_LOCAL:
                event = FileStatusEvent(FileEventTypes.STATUS_CHANGED, task.subject.fullPath, FileStatuses.UPLOADING_TO_CLOUD)
                localTime = time.localtime()
                dstActive = True if localTime.tm_isdst == 1 else False
                data = {"filename": task.subject.filename, "utcModified": task.subject.modified, "userTimezone": time.strftime("%z", localTime), "dstActive": dstActive, "path": task.subject.path, "size": task.subject.size, "fullPath": task.subject.fullPath}
                message = NetworkMessage.Builder(MessageTypes.UPLOAD_FILE).withData(data).withUUID(task.uuid).build()

                self.__fileTaskArchive.removeTask(task.subject.fullPath)
                self.sendNetworkMessage(message)
                self.filesChannel.emit(event)
            elif task.taskType == FileStatuses.DOWNLOADING_TO_LOCAL:
                self.__fileTaskArchive.removeTask(task.subject.fullPath)
                self.__fileSyncService.finalizeDownload(task)
            else:
                raise Exception(f"Unknown tasktype received from sshService: {task.taskType}")

    def __onLocalFileStatusChanged(self, event):
        self.filesChannel.emit(event)
