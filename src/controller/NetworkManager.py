import paramiko
from PyQt4 import QtCore

class NetworkManager(QtCore.QObject):

    def printMessage(self, message):
        print message
