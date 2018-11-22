from src.controller.NetworkManager import NetworkManager
from src.controller.FileManager import FileManager

from PyQt4 import QtCore


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
        self.__setupNetworkManager()
        self.__setupFileManager()

    def __setupNetworkManager(self):
        self.__managers['network_manager'] = NetworkManager()
        self.__threadPool['network_thread'] = QtCore.QThread()
        self.__managers['network_manager'].moveToThread(self.__threadPool['network_thread'])
        self.__threadPool['network_thread'].started.connect((self.__managers['network_manager']).start)
        (self.__threadPool['network_thread']).start()

    def __setupFileManager(self):
        self.__managers['file_manager'] = FileManager(self.getNetworkManager())
        self.__threadPool['file_manager'] = QtCore.QThread()

        self.__managers['file_manager'].moveToThread(self.__threadPool['file_manager'])
        self.__threadPool['file_manager'].started.connect((self.__managers['file_manager']).start)
        (self.__threadPool['file_manager']).start()

    def getNetworkManager(self):
        return self.__managers['network_manager']

    def getFileManager(self):
        return self.__managers['file_manager']

    def shutDown(self):
        (self.__managers['network_manager']).stop()
        (self.__threadPool['network_manager']).stop()
        (self.__managers['file_manager']).stop()
        (self.__threadPool['file_manager']).stop()