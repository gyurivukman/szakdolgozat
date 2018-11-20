import paramiko
from PyQt4 import QtCore
import time

class NetworkManager(QtCore.QObject):
    lofasz = QtCore.pyqtSignal()
    def __init__(self, *args, **kwargs):
        super(NetworkManager, self).__init__()

    def startPrinting(self):
        while(True):
            self.lofasz.emit()
            time.sleep(3)
