import socket
import select
import time
import logging
import random
import string
import os
import asyncio

from datetime import datetime
from uuid import uuid4
from queue import Queue, Empty

import paramiko
from Crypto.Cipher import AES
from msgpack import Packer, Unpacker
from PyQt5.QtCore import QObject, QSettings, pyqtSignal

from model.file import FileStatuses
from model.task import FileTask
from model.networkevents import ConnectionEventTypes, ConnectionEvent
from model.message import NetworkMessage, MessageTypes
from model.permission import WorkspacePermissionValidator


logger = logging.getLogger(__name__)


class NetworkClient(QObject):
    messageArrived = pyqtSignal(NetworkMessage)
    connectionStatusChanged = pyqtSignal(ConnectionEvent)

    def __init__(self, outgoing_queue):
        super().__init__()
        self._CHUNK_SIZE = 2048
        self._outgoing_queue = outgoing_queue
        self._hostInfo = None
        self._shouldRun = True
        self._logger = logger.getChild("NetworkClient")

        self._key = None
        self._encoder = None
        self._decoder = None

        self._socket = None
        self._isConnected = False

        self._packer, self._unpacker = Packer(), Unpacker()
        self._input, self._output, self._error = [], [], []

    def run(self):
        while self._shouldRun:
            if self._isConnected:
                try:
                    readable, writable, in_error = select.select(self._input, self._output, self._error, 1)
                    self._handleIncomingMessage(readable)
                    self._handleOutgoingMessage(writable)
                    self._handleErroneousSocket(in_error)
                except ConnectionError as e:
                    self._logger.error(f"Server disconnected: {e}")
                    self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.NETWORK_DISCONNECTED, {"message": str(e)}))
                    self._handleErroneousSocket([self._socket])
            else:
                time.sleep(0.02)
        if self._isConnected:
            self.disconnect()

    def connect(self):
        self._socket = self._createNewSocket()
        self._setupConnection()
        self._setupSession()

    def setNetworkInformation(self, address, port, aesKey):
        self._hostInfo = (address, port)
        self._key = aesKey

    def _setupConnection(self):
        self._connect()
        self._input.append(self._socket)
        self._output.append(self._socket)

    def _setupSession(self):
        self._logger.debug("Starting handshake...")
        handShakeDone = False

        while not handShakeDone:
            data = self._socket.recv(1024)
            if data:
                self._unpacker.feed(data)
                for sessionMessage in self._unpacker:
                    handShakeDone = True
                    self._processSessionMessage(sessionMessage)
            else:
                self.disconnect()

    def _processSessionMessage(self, sessionMessage):
        self._encoder = AES.new(self._key, mode=AES.MODE_CFB, iv=sessionMessage['iv'])
        self._decoder = AES.new(self._key, mode=AES.MODE_CFB, iv=sessionMessage['iv'])
        decoded = self._decoder.decrypt(sessionMessage['encodeTest'])

        if decoded == sessionMessage['iv']:
            self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.NETWORK_HANDSHAKE_SUCCESSFUL, None))
            self._logger.debug("Successfully set up session!")
            self._isConnected = True
        else:
            message = f"Wrong Aeskey! Sessionkey: {sessionMessage['iv']} , Decoded: {decoded}"
            self._logger.error(message)
            self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.NETWORK_CONNECTION_ERROR, {"message": "Wrong AES key!"}))
            self.disconnect()

    def _createNewSocket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        return sock

    def _connect(self):
        self._logger.debug("Connecting to server")
        self._socket.connect(self._hostInfo)
        self._logger.debug("Connected")
        self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.NETWORK_CONNECTED, None))

    def _handleIncomingMessage(self, readable):
        for s in readable:
            data = s.recv(self._CHUNK_SIZE)
            if data:
                decrypted = self._decoder.decrypt(data)
                self._unpacker.feed(decrypted)
                for message in self._unpacker:
                    msg_obj = NetworkMessage(message)
                    self.messageArrived.emit(msg_obj)
            else:
                self._logger.info("Lost connection to the server!")
                self.disconnect()
                disconnectionEvent = ConnectionEvent(ConnectionEventTypes.NETWORK_DISCONNECTED, None)
                self.connectionStatusChanged.emit(disconnectionEvent)

    def _handleOutgoingMessage(self, writable):
        for s in writable:
            try:
                msg_obj = self._outgoing_queue.get_nowait()
                serialized = self._packer.pack(msg_obj.raw)
                encrypted = self._encoder.encrypt(serialized)
                if self._shouldRun:
                    s.sendall(encrypted)
                    self._logger.debug(f"Message sent. ({msg_obj.header.messageType.name})")
                self._outgoing_queue.task_done()
            except Empty:
                time.sleep(0.02)

    def disconnect(self):
        self._logger.debug("Disconnecting")
        self._isConnected = False
        self._input = []
        self._output = []
        self._socket.close()

    def _handleErroneousSocket(self, in_error):
        for s in in_error:
            self.disconnect()

    def stop(self):
        self._logger.debug("Stopping")
        self._shouldRun = False


class SshClient(QObject):
    connectionStatusChanged = pyqtSignal(ConnectionEvent)
    taskCompleted = pyqtSignal(FileTask)

    def __init__(self, fileSyncer, taskQueu):
        super().__init__()
        self.__UPLOAD_CHUNK_SIZE = 1024
        self.__DOWNLOAD_CHUNK_SIZE = 1024

        self.__shouldRun = True
        self.__fileSyncer = fileSyncer
        self.__tasks = taskQueu
        self.__logger = logger.getChild("SshClient")
        self.__isConnected = False

        self.__hostname = None
        self.__port = 22
        self.__username = None
        self.__password = None
        self.__workSpacePath = None
        self.__userID = None
        self.__userGID = None

        self.__client = paramiko.client.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__sftp = None

        self.__currentTask = None

    def run(self):
        while self.__shouldRun:
            if self.__isConnected:
                try:
                    if not self.__currentTask:
                        self.__currentTask = self.__tasks.get_nowait()
                    self.__handleCurrentTask()
                    self.__tasks.task_done()
                except Empty:
                    time.sleep(0.02)
            else:
                time.sleep(0.02)
        self.disconnect()

    def connect(self):
        self.__logger.debug("Connecting to SSH")
        self.__client.connect(self.__hostname, self.__port, self.__username, self.__password)
        self.__sftp = self.__client.open_sftp()
        self.__logger.debug("SSH Connected")
        self.__isConnected = True
        self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.SSH_CONNECTED, None))

    def stop(self):
        self.__logger.debug("Stopping")
        self.__shouldRun = False

    def disconnect(self):
        self.__client.close()
        if self.__sftp:
            self.__sftp.close()
        self.__isConnected = False

    def setSSHInformation(self, hostname, username, password):
        self.__hostname = hostname
        self.__username = username
        self.__password = password

    def setWorkspace(self, path):
        self.__workSpacePath = path

    def cleanRemoteWorkspace(self):
        if self.__isConnected and self.__workSpacePath:
            self.__cleanRemoteWorkspace(self.__workSpacePath)
        elif not self.__isConnected:
            raise Exception("SSH client is not connected. Call 'connect' first.")
        else:
            raise Exception("Workspace not set. Call 'setWorkspace' first.")

    def __handleCurrentTask(self):
        self.__logger.debug(f"New task: ({self.__currentTask.taskType.name}, {self.__currentTask.subject.fullPath})")
        if self.__currentTask.taskType == FileStatuses.UPLOADING_FROM_LOCAL:
            self.__handleUpload()
        elif self.__currentTask.taskType == FileStatuses.DOWNLOADING_TO_LOCAL:
            self.__handleDownload()
        else:
            self.__logger.debug(f"Unknown task! {self.__currentTask}")
        if not self.__currentTask.stale:
            self.__logger.debug(f"Task done! ({self.__currentTask.taskType.name} {self.__currentTask.subject.fullPath})")
        self.taskCompleted.emit(self.__currentTask)
        self.__currentTask = None

    def __handleUpload(self):
        with self.__sftp.open(self.__currentTask.uuid, "wb") as remoteFileHandle:
            localFilePath = f"{QSettings().value('syncDir/path')}/{self.__currentTask.subject.fullPath}"
            with open(localFilePath, "rb") as localFileHandle:
                data = localFileHandle.read(self.__UPLOAD_CHUNK_SIZE)
                while data and self.__shouldRun and not self.__currentTask.stale:
                    remoteFileHandle.write(data)
                    data = localFileHandle.read(self.__UPLOAD_CHUNK_SIZE)
        if not self.__currentTask.stale:
            self.__sftp.rename(f"{self.__sftp.getcwd()}/{self.__currentTask.uuid}", f"{self.__workSpacePath}/server/{self.__currentTask.uuid}")
        else:
            path = f"{self.__sftp.getcwd()}/{self.__currentTask.uuid}"
            self.__logger.info(f"Task got cancelled, removing remote path: {path}")
            self.__sftp.remove(path)

    def __handleDownload(self):
        syncDir = QSettings().value('syncDir/path')

        absoluteTargetPath = f"{syncDir}/.{self.__currentTask.uuid}"

        with self.__sftp.open(self.__currentTask.uuid, "rb") as remoteFileHandle:
            with open(absoluteTargetPath, "wb") as localFileHandle:
                data = remoteFileHandle.read(self.__DOWNLOAD_CHUNK_SIZE)
                while data and self.__shouldRun and not self.__currentTask.stale:
                    localFileHandle.write(data)
                    data = remoteFileHandle.read(self.__DOWNLOAD_CHUNK_SIZE)

    def __cleanRemoteWorkspace(self, path):
        stdin, stdout, stderr = self.__client.exec_command(f"ls -ld {path}")
        permissionResult = [line for line in stdout][0]

        stdin, stdout, stderr = self.__client.exec_command(f"groups {self.__username}")
        membershipResult = [line for line in stdout][0]

        permissionValidator = WorkspacePermissionValidator(self.__username, path, permissionResult, membershipResult)
        permissionValidator.validate()

        clientWorkspacePath = f"{path}/client"

        self.__sftp.chdir(clientWorkspacePath)
        self.__client.exec_command(f"rm -rf {clientWorkspacePath}/*")
