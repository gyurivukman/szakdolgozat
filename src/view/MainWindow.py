from PyQt4 import QtGui, QtCore
from src.controller.settings import Settings
from UploadsWidget import UploadsWidget
from FirstConfigPanel import FirstConfigPanel


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

    def __setupWidgets(self):
        self.settings = QtCore.QSettings()
        if self.__isFirstStart():
            self.settings.setValue('is_first_start', True)
            self.setFixedSize(400, 550)
            self.settings.sync()
            firstConfigPanel = FirstConfigPanel()
            firstConfigPanel.firstConfigFinished.connect(self.__onFinishedFirstConfig)
            self.setCentralWidget(firstConfigPanel)
        else:
            self.__setupUploadsWidget()
            
    def __setupUploadsWidget(self):
        self.__uploadsWidget = UploadsWidget(self)
        self.setFixedSize(400, 400)
        self.setCentralWidget(self.__uploadsWidget)

    def __isFirstStart(self):
        isFirstStart = not self.settings.contains('is_first_start') or self.settings.contains('is_first_start') and self.settings.value('is_first_start').toBool()
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