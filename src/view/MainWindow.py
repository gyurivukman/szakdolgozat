from PyQt4 import QtGui, QtCore
from src.controller.settings import Settings
from LoginForm import LoginForm
from UploadsWidget import UploadsWidget
from FirstConfigPanel import FirstConfigPanel


class MainWindow(QtGui.QMainWindow):

    def __init__ (self, *args, **kwargs):
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
            self.settings.sync()
            firstConfigPanel = FirstConfigPanel()
            firstConfigPanel.firstConfigFinished.connect(self.__onFinishedFirstConfig)
            self.setCentralWidget(FirstConfigPanel())

        else:
            print "Not First Start"
            # self.settings.remove("is_first_start")
            #self.__uploadsWidget = UploadsWidget(self)
            #self.setCentralWidget(self.__uploadsWidget)

    def __isFirstStart(self):
        isFirstStart = not self.settings.contains('is_first_start') or self.settings.contains('is_first_start') and self.settings.value('is_first_start').toBool()
        return isFirstStart

    def __onFinishedFirstConfig(self):
        self.__uploadsWidget = UploadsWidget(self)
        self.setCentralWidget(self.__uploadsWidget)

    def show(self):
        # screenSize = QtCore.QCoreApplication.instance().desktop().screenGeometry()
        # self.move((screenSize.width()/2)-(self.width()/4), (screenSize.height()/2)-(self.height()/4))
        self.setVisible(True)

    def closeEvent(self, event):
        event.ignore()
        self.hide()