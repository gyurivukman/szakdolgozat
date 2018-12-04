import socket
import select
import time
import sys
import json

from MessageEncoder import MessageEncoder
from messagehandlers.KeepAliveMessageHandler import KeepAliveMessageHandler
from messagehandlers.GetFileListMessageHandler import GetFileListMessageHandler
from messagehandlers.UploadFileMessageHandler import UploadFileMessageHandler
from messagehandlers.DownloadFileMessageHandler import DownloadFileMessageHandler
from messagehandlers.DeleteFileMessageHandler import DeleteFileMessageHandler
from messagehandlers.CheckFileMessageHandler import CheckFileMessageHandler
from messagehandlers.AccountUploadMessageHandler import AccountUploadMessageHandler

# TODO Upload,Download,Delete handlers, optionally rename handler


class CryptStorePiServer(object):

    def __init__(self, port, encryptionKey):
        self.port = port
        self.__client = None
        self.buffer = []
        self.shouldRun = True
        self.__messageEncoder = MessageEncoder(encryptionKey)
        self.__setupServerConnection()
        self.__initMessageHandlers()

    def start(self):
        while self.shouldRun:
            if not self.__client:
                self.__waitForConnection()
            else:
                messageFragment = self.__client.recv(1024)
                if(messageFragment):
                    self.__handleMessageFragment(messageFragment)
                else:
                    self.__client = None

    def __setupServerConnection(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = ('localhost', self.port)
        self.serverSocket.bind(server_address)
        self.serverSocket.listen(1)

    def __initMessageHandlers(self):
        self.__messageHandlers = {
            "keep_alive": KeepAliveMessageHandler(),
            "get_file_list": GetFileListMessageHandler(),
            "upload_file": UploadFileMessageHandler(),
            "download_file": DownloadFileMessageHandler(),
            "delete_file": DeleteFileMessageHandler(),
            "check_file": CheckFileMessageHandler(),
            "account_upload": AccountUploadMessageHandler()
        }

    def __waitForConnection(self):
        self.__client, self.__client_address = self.serverSocket.accept()

    def __handleMessageFragment(self, messageFragment):
        self.buffer.append(messageFragment)
        if ";" in messageFragment:
            encrypted = self.__sliceMessageBuffer()
            decrypted = self.__messageEncoder.decryptMessage(encrypted)
            self.__handleMessage(decrypted)

    def __handleMessage(self, message):
            print "handling message: "+str(message)
            result = (self.__messageHandlers[message["type"]]).handleMessage(message)
            print "message handling result: "+str(result)
            encryptedRes = self.__messageEncoder.encryptMessage(result)
            self.__client.sendall(encryptedRes)

    def __sliceMessageBuffer(self):
        unsliced = "".join(self.buffer)
        slices = unsliced.split(";")
        self.buffer = []
        if len(slices) > 1:
            self.buffer.append(slices[1])
        return slices[0]

    def stop(self):
        self.shouldRun = False
        #TODO close socket.
        sys.exit(0)
