import socket
import select
import time
import logging
import random
import string

from datetime import datetime
from uuid import uuid4
from queue import Queue, Empty

from Crypto.Cipher import AES
from msgpack import Packer, Unpacker
from PyQt5.QtCore import QObject, pyqtSignal

from model.events import ConnectionEventTypes, ConnectionEvent


logger = logging.getLogger(__name__)


class NetworkClient(QObject):
    messageArrived = pyqtSignal(object)
    connectionStatusChanged = pyqtSignal(object)

    def __init__(self, address, port, aesKey, chunkSize):
        super().__init__()
        self._CHUNK_SIZE = chunkSize
        self._hostInfo = (address, port)
        self._shouldRun = True
        self._logger = logger.getChild("NetworkClient")

        self._key = aesKey
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
                except (Exception, BrokenPipeError) as e:
                    self._logger.error(f"Server disconnected: {e}")
                    self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.DISCONNECTED, {"message": str(e)}))
                    self._handleErroneousSocket([self._socket])
            else:
                time.sleep(1)
        self._socket.close()

    def connect(self):
        self._socket = self._createNewSocket()
        self._setupConnection()
        self._setupSession()

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
                for iv in self._unpacker:
                    self._logger.debug(f"Handshake done, received IV: {iv}")
                    self._encoder = AES.new(self._key, mode=AES.MODE_CFB, iv=iv)
                    self._decoder = AES.new(self._key, mode=AES.MODE_CFB, iv=iv)
                    handShakeDone = True
                    self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.HANDSHAKE_SUCCESSFUL, None))
            else:
                self._disconnect()

    def _createNewSocket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        return sock

    def _connect(self):
        self._logger.debug("Connecting to server")
        self._socket.connect(self._hostInfo)
        self._isConnected = True
        self._logger.debug("Connected")
        self.connectionStatusChanged.emit(ConnectionEvent(ConnectionEventTypes.CONNECTED, None))

    def _handleIncomingMessage(self, readable):
        for s in readable:
            data = s.recv(self._CHUNK_SIZE)
            if data:
                decrypted = self._decoder.decrypt(data)
                self._unpacker.feed(decrypted)
                for message in self._unpacker:
                    message['source'] = "SERVER"
                    self.messageArrived.emit(message)
            else:
                self._disconnect()

    def _handleOutgoingMessage(self, writable):
        for s in writable:
            message = self._generateRandomMessage()
            serialized = self._packer.pack(message)
            encrypted = self._encoder.encrypt(serialized)
            if self._shouldRun:
                s.sendall(encrypted)
                self._logger.info("Message sent.")
            time.sleep(2)

    def _disconnect(self):
        self._isConnected = False
        self._input = []
        self._output = []

    def _handleErroneousSocket(self, in_error):
        for s in in_error:
            s.close()
            self._disconnect()

    def _generateRandomMessage(self):
        return {
            "uuid": uuid4().hex,
            "filePath": ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(1, 100))),
            "size": random.randint(1, 1000000000),
            "lastmodified": random.randint(0, 2**32)
        }

    def stop(self):
        self._logger.debug("Stopping")
        self._shouldRun = False


class SshClient(QObject):

    def __init__(self, fileSyncer):
        super().__init__()
        self._shouldRun = True
        self._fileSyncer = fileSyncer
        self._tasks = Queue()
        self._logger = logger.getChild("SshClient")

    def run(self):
        while self._shouldRun:
            time.sleep(2)

    def stop(self):
        self._shouldRun = False
