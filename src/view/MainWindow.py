from PyQt4 import QtGui, QtCore
from src.controller.settings import Settings
from LoginForm import LoginForm
from MainWidget import MainWidget


class MainWindow(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.__setup()
        self.show()

    def __setup(self):
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QtGui.QIcon('./resources/logo.png'))
        self.__setBackgroundColor()
        #TODO: If firstLaunch,settings form, then if not logged in loginform then mainWidget.
        if(True):
            self.__setupLoginFormView()
            self.setFixedSize(400, 300)
        else:
            self.__setupUploadsView()

    def __setBackgroundColor(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self.setPalette(palette)

    def __onSuccessfulLogin(self):
        self.hide()
        self.__setupUploadsView()
        self.show()

    def __setupUploadsView(self):
        self.__setupScrollArea()
        self.setCentralWidget(self.scrollArea)

    def __setupScrollArea(self):
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.__setupScrollContent()

    def __setupScrollContent(self):
        scrollContent = QtGui.QWidget(self.scrollArea)
        scrollContentLayout = QtGui.QVBoxLayout(scrollContent)
        #TODO Actual items/custom widget!
        for item in range(50):
            q = QtGui.QWidget(scrollContent)
            l = QtGui.QHBoxLayout(q)
            l.addWidget(QtGui.QLabel(str(item)))
            q.setLayout(l)
            scrollContentLayout.addWidget(q)
        scrollContentLayout.addStretch()

        self.scrollArea.setWidget(scrollContent)

    def __setupLoginFormView(self):
        self.loginForm = LoginForm(self)
        self.loginForm.loggedIn.connect(self.__onSuccessfulLogin)
        self.setCentralWidget(self.loginForm)

    def show(self):
        if(True):
            resolution = QtCore.QCoreApplication.instance().desktop().screenGeometry()
            posX = (resolution.width()/2) - (self.width()/2)
            posY = (resolution.height()/2) - (self.height()/2)

            self.move(posX, posY)
            self.setVisible(True)
        else:
            pass

    def closeEvent(self, event):
        event.ignore()
        self.hide()