#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui, QtCore
from src.view.SystemTrayIcon import SystemTrayIcon
from src.view.MainWindow import MainWindow

from src.controller.settings import Settings

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
    main_window = MainWindow(flags=flags)

    trayIcon = SystemTrayIcon(QtGui.QIcon("./resources/logo.png"), main_window)
    trayIcon.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()