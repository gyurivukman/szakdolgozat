import socket
import select
import time
import logging
import random
import string

from datetime import datetime
from uuid import uuid4
from queue import Queue, Empty

import paramiko
from Crypto.Cipher import AES
from msgpack import Packer, Unpacker
from PyQt5.QtCore import QObject, QSettings, pyqtSignal

from model.events import ConnectionEventTypes, ConnectionEvent
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
                time.sleep(1)
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
                self.disconnect()

    def _handleOutgoingMessage(self, writable):
        for s in writable:
            try:
                msg_obj = self._outgoing_queue.get_nowait()
                serialized = self._packer.pack(msg_obj.raw)
                encrypted = self._encoder.encrypt(serialized)
                if self._shouldRun:
                    s.sendall(encrypted)
                    self._logger.debug(f"Message sent. ({msg_obj.header.messageType})")
                self._outgoing_queue.task_done()
            except Empty:
                time.sleep(0.5)

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

    def enqueuMessage(self, message):
        self._outgoing_queue.put(message)


class SshClient(QObject):
    connectionStatusChanged = pyqtSignal(ConnectionEvent)
    fileStatusChanged = pyqtSignal(object) # TODO

    def __init__(self, fileSyncer):
        super().__init__()
        self._shouldRun = True
        self._fileSyncer = fileSyncer
        self._tasks = Queue()
        self._logger = logger.getChild("SshClient")
        self._isConnected = False

        self._hostname = None
        self._port = 22
        self._username = None
        self._password = None

        self._client = paramiko.client.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._sftp = None

        self._currentTask = None

    def run(self):
        while self._shouldRun:
            if self._isConnected:
                try:
                    if not self._currentTask:
                        self._currentTask = self._tasks.get_nowait()
                    self._handleCurrentTask()
                except Empty:
                    time.sleep(0.5)
            else:
                time.sleep(0.5)
        self.disconnect()

    def connect(self):
        self._logger.debug("Connecting to SSH")
        self._client.connect(self._hostname, self._port, self._username, self._password)
        self._sftp = self._client.open_sftp()
        self._logger.debug("SSH Connected")
        self._isConnected = True
        self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.SSH_CONNECTED, None))

    def stop(self):
        self._logger.debug("Stopping")
        self._shouldRun = False

    def disconnect(self):
        self._client.close()
        if self._sftp:
            self._sftp.close()
        self._isConnected = False

    def setSSHInformation(self, hostname, username, password):
        self._hostname = hostname
        self._username = username
        self._password = password

    def _handleCurrentTask(self):
        print("Handling current task!")

    def cleanRemoteWorkspace(self, path):
        if self._isConnected:
            self.__cleanRemoteWorkspace(path)
        else:
            raise Exception("SSH client is not connected. call 'connect' first.")

    def __cleanRemoteWorkspace(self, path):
        settings = QSettings()
        username = settings.value("ssh/username")

        stdin, stdout, stderr = self._client.exec_command(f"ls -ld {path}")
        permissionResult = [line for line in stdout][0]

        stdin, stdout, stderr = self._client.exec_command(f"groups {username}")
        membershipResult = [line for line in stdout][0]

        permissionValidator = WorkspacePermissionValidator(username, path, permissionResult, membershipResult)
        permissionValidator.validate()

        clientWorkspacePath = f"{path}/client/"

        self._sftp.chdir(clientWorkspacePath)
        self._client.exec_command(f"rm -rf {clientWorkspacePath}/*")
