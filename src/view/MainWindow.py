from PyQt4 import QtGui, QtCore
from src.controller.settings import Settings
from LoginForm import LoginForm
from UploadsWidget import UploadsWidget


class MainWindow(QtGui.QMainWindow):

    def __init__ (self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QtGui.QIcon("./resources/logo.png"))
        self.__setBackgroundColor()
        self.__settings = Settings()
        #self.__initLoginForm()
        self.__uploadsWidget = UploadsWidget(self)
        self.setCentralWidget(self.__uploadsWidget)
        self.setAcceptDrops(True)
        self.show()

    def __setBackgroundColor(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self.setPalette(palette)
    
    def __onSuccessfulLogin(self):
        self.hide()
        self.__uploadsWidget = UploadsWidget(self)
        self.setCentralWidget(self.__uploadsWidget)
        self.show()

    def __initLoginForm(self):
        self.__loginForm = LoginForm(self)
        self.__loginForm.loggedIn.connect(self.__onSuccessfulLogin)
        self.setCentralWidget(self.__loginForm)

    def show(self):
        screenSize = QtCore.QCoreApplication.instance().desktop().screenGeometry()
        # self.move((screenSize.width()/2)-(self.width()/4), (screenSize.height()/2)-(self.height()/4))
        self.setVisible(True)

    def closeEvent(self, event):
        event.ignore()
        self.hide()