import logging
import time

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QSettings, QCoreApplication, QSize
from PyQt5.QtGui import QIcon

from model.events import ConnectionEvent, ConnectionEventTypes
from services.hub import ServiceHub
from .infopanels import ConnectionErrorPanel
from .loaders import LoaderWidget


class MainWindow(QMainWindow):
    __FIRST_START_SIZE = QSize(1280, 720)
    __NORMAL_SIZE = QSize(360, 720)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loader = LoaderWidget(360, 720, "Connecting to server")
        self._errorPanel = None
        self._settings = QSettings()
        self._serviceHub = ServiceHub()
        self._serviceHub.filesChannel.connect(self._onFileStatusChanged)
        self._serviceHub.networkStatusChannel.connect(self._onNetworkStatusChanged)
        self._logger = logging.getLogger(__name__).getChild("MainWindow")

        self.__errorDialog = None

    def initGUI(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background:#FFFFFF")
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QIcon('view/assets/logo.png'))
        self._setupForRegularView()
        self.show()
        self._serviceHub.startAllServices()
        self._connect()

    def _connect(self):
        self._serviceHub.connect()

    # def __setupForFirstStart(self):
    #     screenSize = QCoreApplication.instance().desktop().screenGeometry()
    #     self.setFixedSize(self.__FIRST_START_SIZE)
    #     self.__moveToCenter(screenSize)
    #     self.setCentralWidget(FirstStartWizard(self))
    #     self.__taskManager.start()

    def _moveToCenter(self, screenSize):
        posX = (screenSize.width() / 2) - (self.width() / 2)
        posY = (screenSize.height() / 2) - (self.height() / 2)
        self.move(posX, posY)

    def _setupForRegularView(self):
        screenSize = QCoreApplication.instance().desktop().screenGeometry()
        self.setFixedSize(self.__NORMAL_SIZE)
        self.setCentralWidget(self._loader)
        self._moveToCenter(screenSize)

    def _createErrorPanel(self):
        panel = ConnectionErrorPanel()
        panel.setFixedSize(360, 720)

        panel.retry.connect(self._onErrorPanelRetryClicked)

        return panel

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def stop(self):
        self._serviceHub.shutdownAllServices()

    def _onFileStatusChanged(self, event):
        self._logger.info(event)

    def _onNetworkStatusChanged(self, event):
        if event.eventType == ConnectionEventTypes.CONNECTED:
            self._loader.setStatusText("Connected, retrieving session key...")
        elif event.eventType == ConnectionEventTypes.HANDSHAKE_SUCCESSFUL:
            self._loader.setStatusText("Handshake successful, retrieving file list...")
        elif event.eventType == ConnectionEventTypes.CONNECTION_ERROR:
            self._errorPanel = self._createErrorPanel()
            self.setCentralWidget(self._errorPanel)

    def _onErrorPanelRetryClicked(self):
        self._loader = LoaderWidget(360, 720, "Connecting to server")
        self.setCentralWidget(self._loader)
        self._connect()
