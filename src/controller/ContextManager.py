from src.controller.NetworkManager import NetworkManager
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
        self.__managers = {
            'network_manager': None
        }

        self.__threadPool = {
            'network_thread': None
        }
        # self.initNetworkManager()

    def getNetworkManager(self):
        if not self.__managers['network_manager']:
            self.__managers['network_manager'] = NetworkManager()
            self.__threadPool['network_thread'] = QtCore.QThread()
            self.__managers['network_manager'].moveToThread(self.__threadPool['network_thread'])
            self.__threadPool['network_thread'].started.connect((self.__managers['network_manager']).startPrinting)
            (self.__threadPool['network_thread']).start()

        return self.__managers['network_manager']