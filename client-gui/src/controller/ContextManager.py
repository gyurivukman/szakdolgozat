from PyQt4 import QtCore

from SSHManager import SSHManager
from TaskManager import TaskManager
from FileScanner import FileScanner
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
        self.__setupFileScanner()
        self.__setupFileManager()

    def __setupSSHManager(self):
        self.__managers['ssh_manager'] = SSHManager()
        self.__threadPool['ssh_thread'] = QtCore.QThread()
        self.__managers['ssh_manager'].moveToThread(self.__threadPool['ssh_thread'])
        self.__threadPool['ssh_thread'].started.connect((self.__managers['ssh_manager']).start)
        (self.__threadPool['ssh_thread']).start()

    def __setupFileScanner(self):
        self.__managers['filescanner'] = FileScanner()
        self.__threadPool['filescanner'] = QtCore.QThread()
        self.__managers['filescanner'].moveToThread(self.__threadPool['filescanner'])
        self.__threadPool['filescanner'].started.connect((self.__managers['filescanner']).start)

    def __setupCommService(self):
        self.__managers['comm_service'] = CommunicationService()
        self.__threadPool['comm_service'] = QtCore.QThread()
        self.__managers['comm_service'].moveToThread(self.__threadPool['comm_service'])
        (self.__threadPool['comm_service']).start()

    def __setupFileManager(self):
        self.__managers['task_manager'] = TaskManager(self.__getsshManager(), self.__getFileScanner(), self.__getCommService())
        self.__threadPool['task_manager'] = QtCore.QThread()

        self.__managers['task_manager'].moveToThread(self.__threadPool['task_manager'])
        self.__threadPool['task_manager'].started.connect((self.__managers['task_manager']).start)
        (self.__threadPool['task_manager']).start()
        (self.__threadPool['filescanner']).start()
        
    def __getsshManager(self):
        return self.__managers['ssh_manager']

    def __getFileScanner(self):
        return self.__managers['filescanner']

    def __getCommService(self):
        return self.__managers['comm_service']

    def getTaskManager(self):
        return self.__managers['task_manager']

    def shutDown(self):
        (self.__managers['ssh_manager']).stop()
        (self.__threadPool['ssh_manager']).stop()

        (self.__managers['task_manager']).stop()
        (self.__threadPool['task_manager']).stop()

        (self.__managers['filescanner']).stop()
        (self.__threadPool['filescanner']).stop()

        (self.__managers['comm_service']).stop()
        (self.__threadPool['comm_service']).stop()
