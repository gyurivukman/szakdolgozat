import socket
import select
import time
import sys
import json

from Encoder import Encoder
from messagehandlers.KeepAliveMessageHandler import KeepAliveMessageHandler
from messagehandlers.GetFileListMessageHandler import GetFileListMessageHandler
from messagehandlers.UploadFileMessageHandler import UploadFileMessageHandler
from messagehandlers.DownloadFileMessageHandler import DownloadFileMessageHandler
from messagehandlers.DeleteFileMessageHandler import DeleteFileMessageHandler
from messagehandlers.CheckFileMessageHandler import CheckFileMessageHandler
from messagehandlers.AccountUploadMessageHandler import AccountUploadMessageHandler

from DatabaseAccessObject import DatabaseAccessObject

from src.model import MessageTypes as MessageTypes

# TODO Upload,Download,Delete handlers, optionally rename handler


class CryptStorePiServer(object):

    def __init__(self, port):
        self.__port = port
        self.__setup()
        self.__setupServerConnection()
        self.__initMessageHandlers()

    def __setup(self):
        self.__client = None
        self.__buffer = []
        self.__shouldRun = True
        self.__encoder = Encoder()
        self.__dao = DatabaseAccessObject()

    def start(self):
        self.__dao.getAccounts()
        while self.__shouldRun:
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
        server_address = ('localhost', self.__port)
        self.serverSocket.bind(server_address)
        self.serverSocket.listen(1)

    def __initMessageHandlers(self):
        self.__messageHandlers = {
            MessageTypes.KEEP_ALIVE: KeepAliveMessageHandler(),
            MessageTypes.GET_FILE_LIST: GetFileListMessageHandler(),
            MessageTypes.UPLOAD_FILE: UploadFileMessageHandler(),
            MessageTypes.DOWNLOAD_FILE: DownloadFileMessageHandler(),
            MessageTypes.DELETE_FILE: DeleteFileMessageHandler(),
            MessageTypes.CHECK_FILE: CheckFileMessageHandler(),
            MessageTypes.ACCOUNT_UPLOAD: AccountUploadMessageHandler()
        }

    def __waitForConnection(self):
        self.__client, self.__client_address = self.serverSocket.accept()

    def __handleMessageFragment(self, messageFragment):
        self.__buffer.append(messageFragment)
        if ";" in messageFragment:
            encrypted = self.__sliceMessageBuffer()
            decrypted = self.__encoder.decryptMessage(encrypted)
            self.__handleMessage(decrypted)

    def __handleMessage(self, message):
            result = (self.__messageHandlers[message["type"]]).handleMessage(message)
            encryptedRes = self.__encoder.encryptMessage(result)
            self.__client.sendall(encryptedRes)

    def __sliceMessageBuffer(self):
        unsliced = "".join(self.__buffer)
        slices = unsliced.split(";")
        self.__buffer = []
        if len(slices) > 1:
            self.__buffer.append(slices[1])
        return slices[0]

    def stop(self):
        self.__shouldRun = False
        sys.exit(0)
