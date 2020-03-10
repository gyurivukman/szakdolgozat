import logging

from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSettings, QCoreApplication, QSize
from PyQt5.QtGui import QIcon

from services.message import MessageDispatcher

# from view.ConfigurationComponents import FirstStartWizard
# from control.services import TaskManager


class MainWindow(QMainWindow):
    __FIRST_START_SIZE = QSize(1280, 720)
    __NORMAL_SIZE = QSize(360, 720)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background:#FFFFFF")
        self.__settings = QSettings()
        self.__messageDispatcher = MessageDispatcher()
        self.__messageDispatcher.fileStatusChanged.connect(self._onFileStatusChanged)
        self.__logger = logging.getLogger(__name__).getChild("MainWindow")

    def initGUI(self):
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QIcon('view/assets/logo.png'))
        self.__setupForRegularView()
        # if self.__isFirstStart():
        #     self.__setupForFirstStart()
        # else:
        #     self.__setupForRegularView()
        self.show()

    # def __isFirstStart(self):
    #     isFirstStart = not self.__settings.contains('IsFirstStart') or self.__settings.contains('IsFirstStart') and self.__settings.value('IsFirstStart').toBool()
    #     return isFirstStart

    # def __setupForFirstStart(self):
    #     screenSize = QCoreApplication.instance().desktop().screenGeometry()
    #     self.setFixedSize(self.__FIRST_START_SIZE)
    #     self.__moveToCenter(screenSize)
    #     self.setCentralWidget(FirstStartWizard(self))
    #     self.__taskManager.start()

    def __moveToCenter(self, screenSize):
        posX = (screenSize.width() / 2) - (self.width() / 2)
        posY = (screenSize.height() / 2) - (self.height() / 2)
        self.move(posX, posY)

    def __setupForRegularView(self):
        screenSize = QCoreApplication.instance().desktop().screenGeometry()
        self.setFixedSize(self.__NORMAL_SIZE)
        self.setCentralWidget(QLabel("HELLO"))
        self.__moveToCenter(screenSize)
        self.__messageDispatcher.startAllServices()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def stop(self):
        self.__messageDispatcher.shutdownAllServices()

    def _onFileStatusChanged(self, event):
        self.__logger.info(event)
