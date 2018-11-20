import paramiko
from PyQt4 import QtCore
import time


class NetworkManager(QtCore.QObject):
    signal = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(NetworkManager, self).__init__()
        self.message = "Alma"

    def startPrinting(self):
        while(True):
            print self.message
            time.sleep(3)

    def setMessage(self, msg):
        self.message = msg
