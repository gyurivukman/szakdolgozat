import socket
import select
import time
import logging
import random
import string

from datetime import datetime
from uuid import uuid4

from msgpack import Packer, Unpacker
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class NetworkClient(QObject):
    messageArrived = pyqtSignal(object)
    connectionStateChanged = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._CHUNK_SIZE = 2048
        self._address = "localhost"
        self._port = 11000
        self._should_run = True
        self._logger = logger.getChild("NetworkClient")

        self._socket = self._create_new_socket()
        self._is_connected = False

        self._packer, self._unpacker = Packer(), Unpacker()
        self._input, self._output, self._error = [], [], []

    def run(self):
        while self._should_run:
            if not self._is_connected:
                try:
                    self._setupConnection()
                except ConnectionRefusedError:
                    logger.error("Connection refused. Retrying in 2 seconds.")
                    time.sleep(2)
            else:
                try:
                    readable, writable, in_error = select.select(self._input, self._output, self._error, 1)
                    self._handle_incoming_message(readable)
                    self._handle_outgoing_message(writable)
                    self._handle_connection_error(in_error)
                except (Exception, BrokenPipeError) as e:
                    logger.error(f"Server disconnected: {e}")
                    self._handle_connection_error([self._socket])
        self._socket.close()

    def _setupConnection(self):
        self._connect()
        self._is_connected = True
        self._input.append(self._socket)
        self._output.append(self._socket)

    def stop(self):
        self._logger.debug("Stopping")
        self._should_run = False

    def _create_new_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        return sock

    def _connect(self):
        logger.info("Connecting to server")
        self._socket.connect((self._address, self._port))
        logger.info("Connected")

        self._input.append(self._socket)
        self._output.append(self._socket)

    def _handle_incoming_message(self, readable):
        for s in readable:
            data = s.recv(self._CHUNK_SIZE)
            if data:
                self._unpacker.feed(data)
                for message in self._unpacker:
                    message['source'] = "SERVER"
                    self.messageArrived.emit(message)
            else:
                self._disconnect()

    def _handle_outgoing_message(self, writable):
        for s in writable:
            message = self._generateRandomMessage()
            encoded = self._packer.pack(message)
            if self._should_run:
                s.sendall(encoded)
                logger.debug("Message sent.")
            time.sleep(2)

    def _disconnect(self):
        self._is_connected = False
        self._input = []
        self._output = []

    def _handle_connection_error(self, in_error):
        for s in in_error:
            s.close()
            self._disconnect()
            self._socket = self._create_new_socket()

    def _generateRandomMessage(self):
        return {
            "uuid": uuid4().hex,
            "filePath": ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(1, 100))),
            "size": random.randint(1, 1000000000),
            "lastmodified": random.randint(0, 2**32)
        }
