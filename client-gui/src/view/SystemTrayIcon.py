from PyQt4 import QtGui, QtCore

from AboutDialog import AboutDialog


class SystemTrayIcon(QtGui.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)
        self.__setup()

    def __setup(self):
        self.__createAboutDialog()
        self.__setupMenu()
        self.setToolTip("CryptStorePi")
        self.activated.connect(self.__activationHandler)

    def __setupMenu(self):
        menu = QtGui.QMenu()

        openAction = menu.addAction("Open")
        openAction.triggered.connect(self.__openAction)

        settingsAction = menu.addAction("Settings")
        settingsAction.triggered.connect(self.__settingsAction)

        aboutAction = menu.addAction("About")
        aboutAction.triggered.connect(self.__aboutAction)

        exitAction = menu.addAction("Exit")
        exitAction.triggered.connect(self.__exitAction)

        self.setContextMenu(menu)

    def __openAction(self):
        self.parent().show()

    def __settingsAction(self):
        print 'SETTINGS'

    def __aboutAction(self):
        self.__aboutDialog.show()

    def __exitAction(self):
        QtCore.QCoreApplication.quit()

    def __activationHandler(self, reason):
        print "Activated: "+ str(reason)
        if(reason == QtGui.QSystemTrayIcon.DoubleClick):
            self.parent().show()

    def __createAboutDialog(self):
        flags = QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        self.__aboutDialog = AboutDialog(self.parent().parent(), flags=flags)
