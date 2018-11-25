from PyQt4 import QtCore
import socket
import Queue
import time

from src.model.FileTask import FileTaskType


class CommunicationService(QtCore.QObject):

    def __init__(self):
        super(CommunicationService, self).__init__()
        self.__setup()

    def __setup(self):
        self.settings = QtCore.QSettings()
        # self.__setupServerConnection()

    def getFileStatus(self, relativeFilePath):
        #TODO: Check if file exists on remote/check its last modified date.
        return FileTaskType.UPLOAD

    def __deleteRemoteFile(self):
        pass

    def __setupServerConnection(self):
        self.serverConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = self.settings.value('remoteAddress').toString()[0]
        communicationPort = self.settings.value('commPort').toInt()[0]

        self.serverConnection.connect((address, communicationPort))
