import socket
import Queue
import time
import json

from PyQt4 import QtCore

from src.model.ConnectionEvent import ConnectionEvent
from src.model.Task import Task, TaskTypes
from MessageEncoder import MessageEncoder


class CommunicationService(QtCore.QObject):
    taskReportChannel = QtCore.pyqtSignal(object)
    connectionStatusChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(CommunicationService, self).__init__()
        self.__shouldRun = True
        self.__connected = False
        self.__setup()

    def __setup(self):
        self.__settings = QtCore.QSettings()
        self.__buffer = []
        self.__messageEncoder = MessageEncoder()
        self.__taskQueue = Queue.Queue()
        self.__setupServerConnection()

    def enqueuTask(self, task):
        self.__taskQueue.put(task)

    def __deleteRemoteFile(self):
        pass

    def getInitialFileList(self):
        time.sleep(5)
        return None
        # try:
        #     message = self.__messageEncoder.encryptMessage('{"type":"get_file_list"}')
        #     decrypted = None
        #     self.__serverConnection.sendall(message)
        #     receivedFullFileList = False
        #     buffer = []
        #     while not receivedFullFileList:
        #         messageFragment = self.__serverConnection.recv(1024)
        #         if(messageFragment):
        #             self.buffer.append(messageFragment)
        #             if ";" in messageFragment:
        #                 encrypted = ("".join(self.buffer)).rstrip(";")
        #                 decrypted = json.loads(self.__messageEncoder.decryptMessage(encrypted))
        #     return decrypted
        # except socket.error:
        #     self.connectionStatusChannel.emit(ConnectionEvent("Comm", False))
        #     self.__connected = False
        #     self.__setupServerConnection()
        #     self.__connect()

    def __setupServerConnection(self):
        self.__serverConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__remoteAddress = (unicode(self.__settings.value('remoteAddress').toString()).encode("utf8"), self.__settings.value('commPort').toInt()[0])
        self.__serverConnection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        while self.__shouldRun:
            if not self.__connected:
                self.__connect()
            elif not self.__taskQueue.empty():
                self.__currentTask = self.__taskQueue.get()
                self.__handleCurrentTask()
            else:
                self.__sendKeepAlive()
                time.sleep(5)

    def __connect(self):
        while not self.__connected:
            try:
                print "Attempting to connect to {}:{}".format(self.__remoteAddress[0], self.__remoteAddress[1])
                self.__serverConnection.connect(self.__remoteAddress)
                self.__connected = True
                self.connectionStatusChannel.emit(ConnectionEvent("Comm", True))
            except socket.error as e:
                print "failed to connect to {}:{} ,retrying in 5 seconds".format(self.__remoteAddress[0], self.__remoteAddress[1])
                time.sleep(5)

    def __handleCurrentTask(self):
        self.taskReportChannel.emit(Task(taskType=TaskTypes.UPLOAD, subject=self.__currentTask.subject))

    def __sendKeepAlive(self):
        try:
            message = self.__messageEncoder.encryptMessage('{"type":"keepalive"}')
            self.__serverConnection.sendall(message)
            encrypted = self.__serverConnection.recv(100)
        except socket.error:
            self.connectionStatusChannel.emit(ConnectionEvent("Comm", False))
            self.__connected = False
            self.__setupServerConnection()
            self.__connect()

    def close(self):
        self.shouldRun = False
        try:
            self.__serverConnection.close()
        except Exception as unhandled:
            pass
