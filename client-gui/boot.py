#!/usr/bin/python

import sys

from PyQt4 import QtGui, QtCore

from src.view.SystemTrayIcon import SystemTrayIcon
from src.view.MainWindow import MainWindow
from src.controller.ContextManager import ContextManager


def setupOrganization():
    QtCore.QCoreApplication.setOrganizationName('elte')
    QtCore.QCoreApplication.setApplicationName('cryptstorepi')


def main():
    if sys.platform == 'win32':
        import ctypes
        appid = u'elte.cryptstorepi'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    app = QtGui.QApplication(sys.argv)

    setupOrganization()
    flags = QtCore.Qt.CustomizeWindowHint|QtCore.Qt.WindowTitleHint|QtCore.Qt.WindowCloseButtonHint|QtCore.Qt.MSWindowsFixedSizeDialogHint 

    mainWindow = MainWindow(flags=flags)

    trayIcon = SystemTrayIcon(QtGui.QIcon("./resources/logo.png"), mainWindow)
    trayIcon.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    main()