import socket
import select
import time
import shutil
import sys
import json
import thread
import os

from messagehandlers.KeepAliveMessageHandler import KeepAliveMessageHandler
from messagehandlers.GetFileListMessageHandler import GetFileListMessageHandler
from messagehandlers.DeleteFileMessageHandler import DeleteFileMessageHandler
from messagehandlers.AccountUploadMessageHandler import AccountUploadMessageHandler
from messagehandlers.ProgressCheckMessageHandler import ProgressCheckMessageHandler
from messagehandlers.MoveFileMessageHandler import MoveFileMessageHandler

from Encoder import Encoder
from DatabaseAccessObject import DatabaseAccessObject
from LongTaskWorker import LongTaskWorker
from src.model import MessageTypes as MessageTypes


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
        self.__cleanSyncDir()
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
        taskReports = {}
        longTaskWorker = LongTaskWorker(taskReports)
        thread.start_new_thread(longTaskWorker.run, ())
        self.__messageHandlers = {
            MessageTypes.KEEP_ALIVE: KeepAliveMessageHandler().handleMessage,
            MessageTypes.GET_FILE_LIST: GetFileListMessageHandler().handleMessage,
            MessageTypes.UPLOAD_FILE: longTaskWorker.enqueueUploadFileTask,
            MessageTypes.DOWNLOAD_FILE: longTaskWorker.enqueueDownloadFileTask,
            MessageTypes.DELETE_FILE: DeleteFileMessageHandler().handleMessage,
            MessageTypes.PROGRESS_CHECK: ProgressCheckMessageHandler(taskReports).handleMessage,
            MessageTypes.ACCOUNT_UPLOAD: AccountUploadMessageHandler().handleMessage,
            MessageTypes.MOVE_FILE: MoveFileMessageHandler().handleMessage
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
            result = (self.__messageHandlers[message["type"]])(message)
            encryptedRes = self.__encoder.encryptMessage(result)
            self.__client.sendall(encryptedRes)

    def __sliceMessageBuffer(self):
        unsliced = "".join(self.__buffer)
        slices = unsliced.split(";")
        self.__buffer = []
        if len(slices) > 1:
            self.__buffer.append(slices[1])
        return slices[0]
    
    def __cleanSyncDir(self):
        for root, dirs, files in os.walk('/opt/remoteSyncDir'):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        print "Successfully cleaned remote."

    def stop(self):
        self.__shouldRun = False
        sys.exit(0)
