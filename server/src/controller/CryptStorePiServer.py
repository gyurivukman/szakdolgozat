import socket
import select
import time
import sys
import json
from MessageEncoder import MessageEncoder


class CryptStorePiServer(object):

    def __init__(self, port, encryptionKey):
        self.port = port
        self.client = None
        self.buffer = []
        self.shouldRun = True
        self.__messageEncoder = MessageEncoder(encryptionKey)

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
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = ('localhost', self.port)
        self.serverSocket.bind(server_address)
        self.serverSocket.listen(1)

    def __waitForConnection(self):
        self.client, self.client_address = self.serverSocket.accept()

    def __handleMessageFragment(self, messageFragment):
        self.buffer.append(messageFragment)
        if ";" in messageFragment:
            encrypted = self.__sliceMessageBuffer()
            decrypted = json.loads(self.__messageEncoder.decryptMessage(encrypted))
            print decrypted
            self.__handleMessage(decrypted)
    
    def __handleMessage(self, message):
        if message["type"] == "keepalive":
            print "got keepalive message!"
            res = self.__messageEncoder.encryptMessage('{"type":"keepalive"}')
            print "sending ack!"
            self.client.sendall(res)

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
