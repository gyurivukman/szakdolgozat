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
        self.__messageEncoder = MessageEncoder()
        self.__taskQueue = Queue.Queue()
        self.__setupTaskHandlers()
        self.__setupServerConnection()

    def enqueuTask(self, task):
        self.__taskQueue.put(task)

    def __deleteRemoteFile(self):
        pass

    def retrieveResponse(self, message):
        message = self.__messageEncoder.encryptMessage(message)
        decrypted = None
        self.__serverConnection.sendall(message)
        receivedFullMessage = False
        buffer = []
        try:
            while not receivedFullMessage:
                messageFragment = self.__serverConnection.recv(1024)
                if(messageFragment):
                    buffer.append(messageFragment)
                    if ";" in messageFragment:
                        encrypted = ("".join(buffer)).rstrip(";")
                        decrypted = json.loads(self.__messageEncoder.decryptMessage(encrypted))
                        receivedFullMessage = True
                else:
                    raise Exception()
        except:
            self.__handleSocketError()
        return decrypted

    def __handleSocketError(self):
            self.connectionStatusChannel.emit(ConnectionEvent("Comm", False))
            self.__connected = False
            self.__setupServerConnection()
            self.__connect()

    def __setupTaskHandlers(self):
        self.__taskHandlers = {
            TaskTypes.SYNCFILELIST: self.__handleSyncFileListTask,
            TaskTypes.KEEP_ALIVE: self.__sendKeepAlive,
            TaskTypes.EXISTENCE_CHECK: self.__handleExistenceCheckTask
        }

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
            except socket.error:
                print "failed to connect to {}:{} ,retrying in 5 seconds".format(self.__remoteAddress[0], self.__remoteAddress[1])
                time.sleep(5)

    def __handleCurrentTask(self):
        (self.__taskHandlers[self.__currentTask.taskType])()

    def __handleSyncFileListTask(self):
        message = {"type": "get_file_list"}
        response = self.retrieveResponse(message)
        self.taskReportChannel.emit(Task(taskType=TaskTypes.SYNCFILELIST, subject=response))
    
    def __handleExistenceCheckTask(self):
        self.taskReportChannel.emit(Task(taskType=TaskTypes.UPLOAD, subject=self.__currentTask.subject))

    def __sendKeepAlive(self):
        # print "sending Comm keepalive"
        message = {"type": "keep_alive"}
        res = self.retrieveResponse(message)

    def close(self):
        self.shouldRun = False
        try:
            self.__serverConnection.close()
        except Exception as unhandled:
            pass
