from PyQt4 import QtGui, QtCore

from UploadsWidget import UploadsWidget
from FirstConfigPanel import FirstConfigPanel
from src.controller.ContextManager import ContextManager
from src.model.ConnectionEvent import ConnectionEvent
from src.model.ConnectionEventTypes import ConnectionEventTypes


class MainWindow(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.__setupInfos()
        self.__setupTaskManager()
        self.__setupWidgets()
        self.show()

    def __setupInfos(self):
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QtGui.QIcon("./resources/logo.png"))
        self.__setBackgroundColor()

    def __setBackgroundColor(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self.setPalette(palette)

    def __setupTaskManager(self):
        self.__taskManager = (ContextManager()).getTaskManager()
        self.__taskManager.connectionStatusChannel.connect(self.__handleConnectionEvent)

        self.__connectionStates = {
            "SSH": False,
            "Comm": False,
            "Sync": False
        }

    def __handleConnectionEvent(self, event):
            self.__connectionStates[event.subject] = event.value

            isSSHUp = self.__connectionStates["SSH"] is True
            isCommUp = self.__connectionStates["Comm"] is True
            isInSync = self.__connectionStates["Sync"] is True

            if isSSHUp and isCommUp and isInSync:
                self.__setupUploadsWidget()    
            elif isSSHUp and isCommUp and not isInSync:
                self.setCentralWidget(QtGui.QLabel("Syncing filelist..."))
            else:
                self.setCentralWidget(QtGui.QLabel("Connecting..."))
            self.repaint()

    def __setupWidgets(self):
        self.__settings = QtCore.QSettings()
        if self.__isFirstStart():
            self.setFixedSize(400, 600)
            self.__settings.setValue('is_first_start', True)
            self.__settings.sync()
            firstConfigPanel = FirstConfigPanel()
            firstConfigPanel.firstConfigFinished.connect(self.__onFinishedFirstConfig)
            self.setCentralWidget(firstConfigPanel)
        else:
            self.setFixedSize(400, 400)
            self.setCentralWidget(QtGui.QLabel("Connecting..."))

    def __setupUploadsWidget(self):
        self.__uploadsWidget = UploadsWidget(self)
        self.setCentralWidget(self.__uploadsWidget)
        

    def __isFirstStart(self):
        isFirstStart = not self.__settings.contains('is_first_start') or self.__settings.contains('is_first_start') and self.__settings.value('is_first_start').toBool()
        return isFirstStart

    def __onFinishedFirstConfig(self):
        self.__setupUploadsWidget()
        #TODO send acc data to server by queueing up a task for it.

    def show(self):
        screenSize = QtCore.QCoreApplication.instance().desktop().screenGeometry()
        self.move(screenSize.width()-self.width(), 15)
        self.setVisible(True)

    def closeEvent(self, event):
        event.ignore()
        self.hide()