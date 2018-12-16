from PyQt4 import QtGui, QtCore

from UploadsWidget import UploadsWidget
from FirstConfigPanel import FirstConfigPanel
from src.controller.ContextManager import ContextManager
from src.model.ConnectionEvent import ConnectionEvent


class MainWindow(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.__setupInfos()
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

            isSSHUp = self.__connectionStates["SSH"]
            isCommUp = self.__connectionStates["Comm"]
            isInSync = self.__connectionStates["Sync"]

            if isSSHUp and isCommUp and isInSync:
                self.setCentralWidget(self.__uploadsWidget)
                self.__uploadsWidget.show()
            elif isSSHUp and isCommUp and not isInSync:
                self.setCentralWidget(QtGui.QLabel("Syncing file list..."))
            else:
                self.setCentralWidget(QtGui.QLabel("Connecting..."))
            self.repaint()

    def __setupWidgets(self):
        self.__settings = QtCore.QSettings()
        isFirstStart = self.__isFirstStart()
        if isFirstStart:
            self.setFixedSize(400, 600)
            self.__moveToCenter()
            self.__settings.setValue('is_first_start', True)
            self.__settings.sync()
            firstConfigPanel = FirstConfigPanel()
            firstConfigPanel.firstConfigFinished.connect(self.__onFinishedFirstConfig)
            self.setCentralWidget(firstConfigPanel)
        else:
            self.__setupNormalView()
            self.__taskManager.init()

    def __setupNormalView(self):
        self.setFixedSize(500, 400)
        self.__moveToUpperRightCorner()
        self.setCentralWidget(QtGui.QLabel("Connecting..."))
        self.__setupTaskManager()
        self.__uploadsWidget = UploadsWidget()
        self.__uploadsWidget.hide()

    def __isFirstStart(self):
        isFirstStart = not self.__settings.contains('is_first_start') or self.__settings.contains('is_first_start') and self.__settings.value('is_first_start').toBool()
        return isFirstStart

    def __onFinishedFirstConfig(self, accountData):
        self.__setupNormalView()
        self.__taskManager.init(accountData)

    def __moveToCenter(self):
        screenSize = QtCore.QCoreApplication.instance().desktop().screenGeometry()
        posX = (screenSize.width()/2) - (self.width()/2)
        posY = (screenSize.height()/2) - (self.height()/2)
        self.move(posX, posY)

    def __moveToUpperRightCorner(self):
        screenSize = QtCore.QCoreApplication.instance().desktop().screenGeometry()
        posX = screenSize.width() - self.width() - 10
        posY = 25
        self.move(posX, posY)

    def show(self):
        if self.__isFirstStart():
            self.__moveToCenter()
        else:
            self.__moveToUpperRightCorner()
        self.setVisible(True)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
