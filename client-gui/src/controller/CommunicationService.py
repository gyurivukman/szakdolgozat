import socket
import Queue
import time
import json

from PyQt4 import QtCore

from src.model.FileTask import FileTaskType
from MessageEncoder import MessageEncoder


class CommunicationService(QtCore.QObject):
    ready = QtCore.pyqtSignal(bool)
    taskReportChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(CommunicationService, self).__init__()
        self.__shouldRun = True
        self.__connected = False
        self.__setup()

    def __setup(self):
        self.__settings = QtCore.QSettings()
        self.__buffer = []
        self.__messageEncoder = MessageEncoder()
        self.__setupServerConnection()
        self.__taskQueue = Queue.Queue()

    def enqueuFileStatusTask(self, statusTask):
        #TODO: Check if file exists on remote/check its last modified date.
        self.__taskQueue.put(statusTask)

    def __deleteRemoteFile(self):
        pass

    def getInitialFileList(self):
        pass

    def __setupServerConnection(self):
        self.__serverConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__remoteAddress = (unicode(self.__settings.value('remoteAddress').toString()).encode("utf8"), self.__settings.value('commPort').toInt()[0])
        self.__serverConnection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        while self.__shouldRun:
            try:
                if not self.__connected:
                    self.__connect()
                elif not self.__taskQueue.empty():
                    self.__currentTask = self.__taskQueue.get()
                    self.__handleCurrentTask()
                else:
                    time.sleep(5)
            except:
                print "Communications connection dropped!"
                self.__connect()

    def __connect(self):
        while not self.__connected:
            try:
                print "Attempting to connect to {}:{}".format(self.__remoteAddress[0], self.__remoteAddress[1])
                self.__serverConnection.connect(self.__remoteAddress)
                print "Connected!"
                self.__connected = True
                self.ready.emit(True)
            except Exception as e:
                print "failed to connect to {}:{} ,retrying in 5 seconds".format(self.__remoteAddress[0], self.__remoteAddress[1])
                time.sleep(5)

    def __handleCurrentTask(self):
        #TODO proper handlers, only does filecheck now!
        self.taskReportChannel.emit({"todo": FileTaskType.UPLOAD, "data": self.__currentTask})

    def close(self):
        self.shouldRun = False
        try:
            self.serverConnection.close()
        except Exception as unhandled:
            pass
