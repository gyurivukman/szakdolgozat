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
        self.__taskManager.connectionStatusChannel.connect(self.__handleConnectionChangeEvent)

        self.__connectionStates = {
            "SSH": False,
            "Comm": False
        }
        self.__connectingMessage = QtGui.QLabel("Connecting...")

    def __handleConnectionChangeEvent(self, event):
            self.__connectionStates[event.subject] = True if event.eventType == ConnectionEventTypes.CONNECTED else False
            if self.__connectionStates["SSH"] and self.__connectionStates["Comm"]:
                self.setCentralWidget(self.__uploadsWidget)
                self.__uploadsWidget.show()
                self.repaint()
            else:
                self.__uploadsWidget.hide()
                self.setCentralWidget(self.__connectingMessage)
                self.repaint()

    def __setupWidgets(self):
        self.__settings = QtCore.QSettings()
        if self.__isFirstStart():
            self.__settings.setValue('is_first_start', True)
            self.setFixedSize(400, 600)
            self.__settings.sync()
            firstConfigPanel = FirstConfigPanel()
            firstConfigPanel.firstConfigFinished.connect(self.__onFinishedFirstConfig)
            self.setCentralWidget(firstConfigPanel)
        else:
            self.__setupUploadsWidget()
            self.setCentralWidget(self.__connectingMessage)

    def __setupUploadsWidget(self):
        self.__uploadsWidget = UploadsWidget(self)
        self.__uploadsWidget.hide()
        self.setFixedSize(400, 400)

    def __isFirstStart(self):
        isFirstStart = not self.__settings.contains('is_first_start') or self.__settings.contains('is_first_start') and self.__settings.value('is_first_start').toBool()
        return isFirstStart

    def __onFinishedFirstConfig(self):
        self.__setupUploadsWidget()
        self.update()
        self.repaint()

    def show(self):
        screenSize = QtCore.QCoreApplication.instance().desktop().screenGeometry()
        self.move(screenSize.width()-self.width(), 15)
        self.setVisible(True)

    def closeEvent(self, event):
        event.ignore()
        self.hide()