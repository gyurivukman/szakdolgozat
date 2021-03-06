import socket
import select
import logging
import time

from queue import Empty

from msgpack import Packer, Unpacker
from Crypto.Cipher import AES

from .message import MessageDispatcher
from .worker import WorkerPool
from model.message import NetworkMessage, MessageTypes
from model.task import TaskArchive


class Server(object):

    def __init__(self, port, key):
        self._CHUNK_SIZE = 2048
        self._shouldRun = True

        self._port = port
        self._key = key.encode()
        self._server = self._createServerSocket()

        self._inputs = [self._server]
        self._outputs = []

        self._client = None
        self._clientAddress = None

        self._packer = Packer()
        self._unpacker = Unpacker()

        self._encoder = None
        self._decoder = None

        self._logger = logging.getLogger(__name__).getChild("Server")

        self._messageDispatcher = MessageDispatcher()
        self._workerPool = WorkerPool()
        self._taskArchive = TaskArchive()

    def start(self):
        self._workerPool.start()
        self._logger.info("Ready")
        while self._shouldRun:
            readable, writable, inError = select.select(self._inputs, self._outputs, self._inputs)

            self._handleReadable(readable)
            self._handleWritable(writable)
            self._handleError(inError)

    def stop(self):
        self._logger.debug("Shutting down.")
        self._shouldRun = False
        self._server.close()
        if self._client:
            self._client.close()
        self._workerPool.stop()

    def _createServerSocket(self):
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverSocket.bind(("localhost", self._port))
        serverSocket.listen(1)

        return serverSocket

    def _handleReadable(self, readable):
        try:
            for readableSocket in readable:
                if readableSocket is self._server:
                    self._logger.info("Client connecting")
                    if not self._client:
                        self._logger.info("Accepting client")
                        self._acceptClient()
                    else:
                        self._logger.info("Client already connected, rejecting new client..")
                        self._rejectClient()
                else:
                    self._readClientData(readableSocket)
        except ConnectionResetError as e:
            self._handleDisconnect(self._client, e)

    def _readClientData(self, client):
        data = client.recv(self._CHUNK_SIZE)
        if data:
            if client not in self._outputs:
                self._outputs.append(client)
            decrypted = self._decoder.decrypt(data)
            self._unpacker.feed(decrypted)
            self._processIncomingMessages()
        else:
            self._handleDisconnect(client)

    def _handleDisconnect(self, client, error=""):
        self._logger.info(f"Client disconnected {error}. Cleaning up connections and resetting tasks.")
        if client in self._outputs:
            self._outputs.remove(client)
        if client in self._inputs:
            self._inputs.remove(client)
        if client:
            client.close()
        self._client = None
        self._clientAddress = None
        self._taskArchive.clearAllTasks()

    def _processIncomingMessages(self):
        for message in self._unpacker:
            msg_obj = NetworkMessage(message)
            self._messageDispatcher.dispatchIncomingMessage(msg_obj)

    def _acceptClient(self):
        self._client, self._clientAddress = self._server.accept()
        self._inputs.append(self._client)
        self._logger.debug("Client connected")
        self._sendSessionKey()

    def _sendSessionKey(self):
        self._encoder = AES.new(self._key, AES.MODE_CFB)
        self._decoder = AES.new(self._key, AES.MODE_CFB, iv=self._encoder.iv)
        self._logger.debug(f"Setting up session with key: {self._encoder.iv}")
        encoded = self._encoder.encrypt(self._encoder.iv)
        packed = self._packer.pack({"iv": self._encoder.iv, "encodeTest": encoded})
        self._client.sendall(packed)
        self._logger.debug("Session data sent!")

    def _rejectClient(self):
        client, _ = self._server.accept()
        client.close()

    def _handleWritable(self, writable):
        try:
            for s in writable:
                try:
                    msg_obj = self._messageDispatcher.outgoing_message_queue.get_nowait() # TODO Majd refaktor kicsit.
                    serialized = self._packer.pack(msg_obj.raw)
                    encrypted = self._encoder.encrypt(serialized)
                    s.sendall(encrypted)
                    self._messageDispatcher.outgoing_message_queue.task_done() # TODO Majd refaktor kicsit.
                except Empty:
                    time.sleep(1)
        except OSError as e:
            self._handleDisconnect(self._client, e)

    def _handleError(self, inError):
        for s in inError:
            self._logger.error(f"Some error in handleError {s}")
            if s in self._inputs:
                self._inputs.remove(s)
            if s in self._outputs:
                self._outputs.remove(s)
            s.close()
