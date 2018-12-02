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
        self.__managers = {}
        self.__threadPool = {}
        self.__setupSSHManager()
        self.__setupCommService()
        self.__setupTaskManager()
        self.__startDependentServices()

    def __setupSSHManager(self):
        self.__managers['ssh_manager'] = SSHManager()
        self.__threadPool['ssh_thread'] = QtCore.QThread()
        self.__managers['ssh_manager'].moveToThread(self.__threadPool['ssh_thread'])
        self.__threadPool['ssh_thread'].started.connect((self.__managers['ssh_manager']).start)

    def __setupCommService(self):
        self.__managers['comm_service'] = CommunicationService()
        self.__threadPool['comm_service'] = QtCore.QThread()
        self.__managers['comm_service'].moveToThread(self.__threadPool['comm_service'])
        self.__threadPool['comm_service'].started.connect((self.__managers['comm_service']).start)

    def __setupTaskManager(self):
        self.__managers['task_manager'] = TaskManager(self.getsshManager(), self.getCommService())
        self.__threadPool['task_manager'] = QtCore.QThread()

        self.__managers['task_manager'].moveToThread(self.__threadPool['task_manager'])
        self.__threadPool['task_manager'].started.connect((self.__managers['task_manager']).start)
        (self.__threadPool['task_manager']).start()

    def __startDependentServices(self):
        (self.__threadPool['ssh_thread']).start()
        (self.__threadPool['comm_service']).start()

    def getsshManager(self):
        return self.__managers['ssh_manager']

    def getCommService(self):
        return self.__managers['comm_service']

    def getTaskManager(self):
        return self.__managers['task_manager']

    def shutDown(self):
        (self.__managers['ssh_manager']).stop()
        (self.__threadPool['ssh_manager']).stop()

        (self.__managers['task_manager']).stop()
        (self.__threadPool['task_manager']).stop()

        (self.__managers['comm_service']).stop()
        (self.__threadPool['comm_service']).stop()
