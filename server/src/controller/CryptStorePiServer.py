import socket
import select
import time
import sys

from MessageEncoder import MessageEncoder


class CryptStorePiServer(object):

    def __init__(self, port, encryptionKey):
        self.port = port
        self.client = None
        self.encryptionKey = encryptionKey
        self.buffer = []
        self.shouldRun = True
        self.messageEncoder = MessageEncoder()

    def start(self):
        self.__setup()
        while self.shouldRun:
            if not self.client:
                self.__waitForConnection()
            else:
                messageFragment = self.client.recv(1024)
                if(messageFragment):
                    self.__handleMessageFragment(messageFragment)
                else:
                    print "Disconnected."
                    self.client = None

    def __setup(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.serverSocket.setsockopt()
        server_address = ('localhost', self.port)
        self.serverSocket.bind(server_address)
        self.serverSocket.listen(1)

        print self.client

    def __waitForConnection(self):
        self.client, self.client_address = self.serverSocket.accept()

    def __handleMessageFragment(self, messageFragment):
        if ";" in messageFragment:
            message = self.messageEncoder.decryptMessage(self.__sliceMessageBuffer())
        else:
            self.buffer.append

    def __sliceMessageBuffer(self):
        unsliced = "".join(self.buffer)
        slices = unsliced.split(";")
        self.buffer = []
        if len(slices) > 1:
            self.buffer.append(slices[1])

        return slices[0]

    def stop(self, sig):
        self.shouldRun = False
        #TODO close socket.
        sys.exit(0)
