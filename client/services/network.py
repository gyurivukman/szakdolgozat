import socket
import select
import time
import logging
import random
import string

from uuid import uuid4

from msgpack import Packer, Unpacker

logger = logging.getLogger(__name__)


class NetworkClient(object):

    def __init__(self, output_queue):
        self._CHUNK_SIZE = 2048
        self._address = "localhost"
        self._port = 11000
        self._should_run = True

        self._socket = self._create_new_socket()
        self._is_connected = False

        self._packer, self._unpacker = Packer(), Unpacker()
        self._input, self._output, self._error = [], [], []
        self._output_queue = output_queue

    def run(self):
        while self._should_run:
            if not self._is_connected:
                try:
                    self._setupConnection()
                except ConnectionRefusedError:
                    logger.error("Connection refused. Retrying in 5 seconds.")
                    time.sleep(5)
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
                    self._process_message(message)
            else:
                self._disconnect()

    def _handle_outgoing_message(self, writable):
        for s in writable:
            message = self._generateRandomMessage()
            encoded = self._packer.pack(message)
            s.sendall(encoded)
            logger.info("Message sent.")
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

    def _process_message(self, message):
        message['source'] = "SERVER"
        self._output_queue.put(message)

    def _generateRandomMessage(self):
        return {
            "uuid": uuid4().hex,
            "filePath": ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(1, 128))),
            "size": random.randint(1, 1000000000),
            "lastmodified": random.randint(0, 2**32)
        }
