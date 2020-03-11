import socket
import select
import time
import logging
import random
import string

from datetime import datetime
from uuid import uuid4
from queue import Queue, Empty

from msgpack import Packer, Unpacker
from PyQt5.QtCore import QObject, pyqtSignal


logger = logging.getLogger(__name__)


class NetworkClient(QObject):
    messageArrived = pyqtSignal(object)
    connected = pyqtSignal()
    diconnected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._CHUNK_SIZE = 2048
        self._address = "localhost"
        self._port = 11000
        self._shouldRun = True
        self._logger = logger.getChild("NetworkClient")

        self._socket = self._createNewSocket()
        self._isConnected = False

        self._packer, self._unpacker = Packer(), Unpacker()
        self._input, self._output, self._error = [], [], []

    def run(self):
        while self._shouldRun:
            if not self._isConnected:
                try:
                    self._setupConnection()
                except ConnectionRefusedError:
                    logger.error("Connection refused. Retrying in 2 seconds.")
                    time.sleep(2)
            else:
                try:
                    readable, writable, in_error = select.select(self._input, self._output, self._error, 1)
                    self._handleIncomingMessage(readable)
                    self._handleOutgoingMessage(writable)
                    self._handleErroneousSocket(in_error)
                except (Exception, BrokenPipeError) as e:
                    logger.error(f"Server disconnected: {e}")
                    self.diconnected.emit()
                    self._handleErroneousSocket([self._socket])
        self._socket.close()

    def _setupConnection(self):
        self._connect()
        self._isConnected = True
        self._input.append(self._socket)
        self._output.append(self._socket)

    def stop(self):
        self._logger.debug("Stopping")
        self._shouldRun = False

    def _createNewSocket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        return sock

    def _connect(self):
        logger.info("Connecting to server")
        self._socket.connect((self._address, self._port))
        logger.info("Connected")

    def _handleIncomingMessage(self, readable):
        for s in readable:
            data = s.recv(self._CHUNK_SIZE)
            if data:
                self._unpacker.feed(data)
                for message in self._unpacker:
                    message['source'] = "SERVER"
                    self.messageArrived.emit(message)
            else:
                self._disconnect()

    def _handleOutgoingMessage(self, writable):
        for s in writable:
            message = self._generateRandomMessage()
            encoded = self._packer.pack(message)
            if self._shouldRun:
                s.sendall(encoded)
                logger.info("Message sent.")
            time.sleep(2)

    def _disconnect(self):
        self._isConnected = False
        self._input = []
        self._output = []

    def _handleErroneousSocket(self, in_error):
        for s in in_error:
            s.close()
            self._disconnect()
            self._socket = self._createNewSocket()

    def _generateRandomMessage(self):
        return {
            "uuid": uuid4().hex,
            "filePath": ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(1, 100))),
            "size": random.randint(1, 1000000000),
            "lastmodified": random.randint(0, 2**32)
        }


class SshClient(QObject):

    def __init__(self, fileSyncer):
        super().__init__()
        self._shouldRun = True
        self._fileSyncer = fileSyncer
        self._tasks = Queue()
        self._logger = logger.getChild("SshClient")

    def run(self):
        while self._shouldRun:
            self._logger.info("sshClient working")
            if random.randint(0, 100) % 2 == 0:
                self._fileSyncer.poke()
            time.sleep(2)

    def stop(self):
        self._shouldRun = False
