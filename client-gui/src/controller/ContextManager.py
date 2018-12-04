from PyQt4 import QtCore

from SSHManager import SSHManager
from TaskManager import TaskManager
from CommunicationService import CommunicationService


class ContextManagerWrapper(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(ContextManagerWrapper, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ContextManager(object):
    __metaclass__ = ContextManagerWrapper

    def __init__(self):
        self.__setupTaskManager()

    def __setupTaskManager(self):
        self.__taskManager = TaskManager()
        self.__taskManagerThread = QtCore.QThread()

        self.__taskManager.moveToThread(self.__taskManagerThread)
        self.__taskManagerThread.started.connect(self.__taskManager.start)
        self.__taskManagerThread.start()

    def getTaskManager(self):
        return self.__taskManager

    def shutDown(self):
        self.__taskManager.stop()
