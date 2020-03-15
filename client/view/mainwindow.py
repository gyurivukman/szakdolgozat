import logging

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QSettings, QCoreApplication, QSize
from PyQt5.QtGui import QIcon

from model.events import ConnectionEvent, ConnectionEventTypes
from view.dialogs import ConnectionErrorDialog
from services.hub import ServiceHub
from .loaders import LoaderWidget


# from view.ConfigurationComponents import FirstStartWizard


class MainWindow(QMainWindow):
    __FIRST_START_SIZE = QSize(1280, 720)
    __NORMAL_SIZE = QSize(360, 720)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background:#FFFFFF")
        self.__loader = LoaderWidget(360, 720, "Connecting to server")
        self.__errorDialog = None
        self.__settings = QSettings()
        self.__serviceHub = ServiceHub()
        self.__serviceHub.filesChannel.connect(self._onFileStatusChanged)
        self.__serviceHub.networkStatusChannel.connect(self._onNetworkStatusChanged)
        self.__logger = logging.getLogger(__name__).getChild("MainWindow")

        self.__errorDialog = None

    def initGUI(self):
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QIcon('view/assets/logo.png'))
        self.__setupForRegularView()
        self.show()

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
        self.setCentralWidget(self.__loader)
        self.__moveToCenter(screenSize)
        self.__serviceHub.startAllServices()
        self.__serviceHub.connect()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def stop(self):
        self.__serviceHub.shutdownAllServices()

    def _onFileStatusChanged(self, event):
        self.__logger.info(event)

    def _onNetworkStatusChanged(self, event):
        if event.eventType == ConnectionEventTypes.CONNECTED:
            self.__loader.setStatusText("Connected, retrieving session key...")
        elif event.eventType == ConnectionEventTypes.HANDSHAKE_SUCCESSFUL:
            self.__loader.setStatusText("Handshake successful, retrieving file list...")
        elif event.eventType == ConnectionEventTypes.CONNECTION_ERROR:
            self.__loader.setStatusText("Couldn't connect to remote server.")
            self.__errorDialog = ConnectionErrorDialog(messageText=f"{event.data['message']}\n")
            self.__errorDialog.show()