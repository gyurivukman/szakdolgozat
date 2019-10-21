from pprint import pprint

from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt, QSettings, QCoreApplication

from view.ConfigurationComponents import FirstStartWizard
from control.services import TaskManager


class MainWindow(QMainWindow):
    def __init__(self):
        flags = Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint
        super().__init__(flags=flags)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background:#FFFFFF")
        self.__settings = QSettings()
        self.__taskManager = TaskManager()

    def initGUI(self):
        self.setWindowTitle('CryptStorePi')
        if self.__isFirstStart():
            self.__setupForFirstStart()
        else:
            self.__setupForRegularView()
        self.show()

    def __isFirstStart(self):
        isFirstStart = not self.__settings.contains('IsFirstStart') or self.__settings.contains('IsFirstStart') and self.__settings.value('IsFirstStart').toBool()
        return isFirstStart

    def __setupForFirstStart(self):
        screenSize = QCoreApplication.instance().desktop().screenGeometry()
        self.setFixedSize(1280, 720)
        self.__moveToCenter(screenSize)
        self.setCentralWidget(FirstStartWizard(self))
        self.__taskManager.start()

    def __moveToCenter(self, screenSize):
        posX = (screenSize.width() / 2) - (self.width() / 2)
        posY = (screenSize.height() / 2) - (self.height() / 2)
        self.move(posX, posY)

    def __setupRegularView(self):
        pass

    def closeEvent(self, event):
        event.ignore()
        self.hide()