import socket
import select
import logging
import random
import string
import time

from uuid import uuid4

from msgpack import Packer, Unpacker
from Crypto.Cipher import AES


class Server(object):

    def __init__(self):
        self._CHUNK_SIZE = 2048

        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("localhost", 11000))
        self._server.listen(1)
        self._key = b"sixteen byte jey"

        self._shouldRun = True

        self._inputs = [self._server]
        self._outputs = []

        self._client = None
        self._client_address = None

        self._packer = Packer()
        self._unpacker = Unpacker()

        self._encoder = None
        self._decoder = None

        self._logger = logging.getLogger(__name__).getChild("Server")

    def start(self):
        self._logger.info("Ready!")
        while self._shouldRun:
            readable, writable, in_error = select.select(self._inputs, self._outputs, self._inputs)

            self._handle_readable(readable)
            self._handle_writable(writable)
            self._handle_error(in_error)

    def stop(self):
        self._logger.debug("Shutting down.")
        self._shouldRun = False
        self._server.close()
        if self._client:
            self._client.close()

    def _handle_readable(self, readable):
        try:
            for readable_socket in readable:
                if readable_socket is self._server:
                    self._logger.info("Client connecting")
                    self._accept_client() if not self._client else self._reject_client()
                else:
                    self._readClientData(readable_socket)
        except ConnectionResetError:
            self._handle_disconnect(self._client)

    def _readClientData(self, client):
        data = client.recv(self._CHUNK_SIZE)
        if data:
            if client not in self._outputs:
                self._outputs.append(client)
            decrypted = self._decoder.decrypt(data)
            self._unpacker.feed(decrypted)
            self._process_messages()
        else:
            self._handle_disconnect(client)

    def _handle_disconnect(self, client):
        if client in self._outputs:
            self._outputs.remove(client)
        if client in self._inputs:
            self._inputs.remove(client)
        if client:
            client.close()
        self._client = None
        self._client_address = None

    def _process_messages(self):
        for message in self._unpacker:
            self._logger.info(f"Message arrived: {message}")

    def _accept_client(self):
        self._client, self._client_address = self._server.accept()
        self._inputs.append(self._client)
        self._logger.debug("Client connected")
        self._send_session_key()

    def _send_session_key(self):
        self._encoder = AES.new(self._key, AES.MODE_CFB)
        self._decoder = AES.new(self._key, AES.MODE_CFB, iv=self._encoder.iv)
        self._logger.debug(f"Setting up session with key: {self._encoder.iv}")
        encoded = self._encoder.encrypt(self._encoder.iv)
        packed = self._packer.pack({"iv": self._encoder.iv, "encodeTest": encoded})
        self._client.sendall(packed)
        self._logger.debug("Session data sent!")

    def _reject_client(self):
        self._logger.info("Rejecting client")
        client, _ = self._server.accept()
        client.close()

    def _handle_writable(self, writable):
        try:
            for s in writable:
                shouldSendAMessage = random.randint(0, 100) % 2 == 0
                if shouldSendAMessage:
                    message = self._generateRandomMessage()
                    serialized = self._packer.pack(message)
                    encrypted = self._encoder.encrypt(serialized)
                    s.sendall(encrypted)
                    time.sleep(2)
        except (Exception, OSError) as e:
            self._logger.error(f"Client disconnected: {e}")
            self._handle_disconnect(self._client)

    def _handle_error(self, inError):
        for s in inError:
            self._logger.error(f"Some error in handle_error {s}")
            if s in self._inputs:
                self._inputs.remove(s)
            if s in self._outputs:
                self._outputs.remove(s)
            s.close()

    def _generateRandomMessage(self):
        return {
            "uuid": uuid4().hex,
            "message": ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(1, 32))),
        }
