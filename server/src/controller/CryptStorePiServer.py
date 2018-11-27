import socket
import time
import sys


class CryptStorePiServer(object):

    def __init__(self, port, encryptionKey):
        self.port = port
        self.encryptionKey = encryptionKey
        self.buffer = []
        self.shouldRun = True

    def start(self):
        self.__setup()
        while self.shouldRun:
            try:
                messageFragment = self.serverSocket.recv(1024)
            except KeyboardInterrupt:
                self.clientConnection.close()
            finally:
                sys.exit(0)

    def __setup(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', self.port)
        self.serverSocket.bind(server_address)
        self.serverSocket.listen(1)
        self.client, self.client_address = self.serverSocket.accept()

    def stop(self, sig):
        self.shouldRun = False
        #TODO close socket.
        sys.exit(0)
