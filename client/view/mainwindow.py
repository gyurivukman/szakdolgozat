import logging
import time

from PyQt5.QtWidgets import QMainWindow, QAction
from PyQt5.QtCore import Qt, QSettings, QCoreApplication, QSize
from PyQt5.QtGui import QIcon

from model.events import ConnectionEvent, ConnectionEventTypes
from services.hub import ServiceHub
from view.infopanels import ConnectionErrorPanel
from view.loaders import LoaderWidget
from view.firststart import FirstStartWizard

from . import resources


class MainWindow(QMainWindow):
    __FIRST_START_SIZE = QSize(1280, 720)
    __NORMAL_SIZE = QSize(360, 720)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loader = LoaderWidget(360, 720, "Connecting to server")
        self._errorPanel = None
        self._mainPanel = None
        self._settings = QSettings()
        self._serviceHub = ServiceHub()
        self._logger = logging.getLogger(__name__).getChild("MainWindow")

        self.__errorDialog = None

    def initGUI(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background:#FFFFFF")
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QIcon(':logo.png'))
        if self._isFirstStart():
            self._setupForFirstStart()
        else:
            self._setupForRegularView()
            self._serviceHub.startAllServices()
            self._serviceHub.connect("localhost", 11000, b"sixteen byte key")
        self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def stop(self):
        self._serviceHub.shutdownAllServices()

    def _setupForFirstStart(self):
        screenSize = QCoreApplication.instance().desktop().screenGeometry()
        self.setFixedSize(self.__FIRST_START_SIZE)
        self._moveToCenter(screenSize)
        self._mainPanel = FirstStartWizard(self)
        self.setCentralWidget(self._mainPanel)

    def _moveToCenter(self, screenSize):
        posX = (screenSize.width() / 2) - (self.width() / 2)
        posY = (screenSize.height() / 2) - (self.height() / 2)
        self.move(posX, posY)

    def _setupForRegularView(self):
        self._serviceHub.filesChannel.connect(self._onFileStatusChanged)
        self._serviceHub.networkStatusChannel.connect(self._onNetworkStatusChanged)
        screenSize = QCoreApplication.instance().desktop().screenGeometry()
        self._initMenu()
        self.setFixedSize(self.__NORMAL_SIZE)
        self.setCentralWidget(self._loader)
        self._moveToCenter(screenSize)

    def _initMenu(self):
        menuBar = self.menuBar()
        menuBar.setStyleSheet("""QMenu:item:selected{background-color: #e36410;}""")
        fileMenu = menuBar.addMenu("File")

        settingsAction = QAction("Settings", self)
        settingsAction.triggered.connect(self._onSettingsMenuItemClicked)

        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self._onExitMenuItemClicked)
        fileMenu.addAction(settingsAction)
        fileMenu.addAction(exitAction)

    def _createErrorPanel(self):
        panel = ConnectionErrorPanel()
        panel.setFixedSize(360, 720)

        panel.retry.connect(self._onErrorPanelRetryClicked)

        return panel

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
        # TODO qsettingsbol kiolvasni a connect parametereit, újra és újra minden alkalommal.
        self._loader = LoaderWidget(360, 720, "Connecting to server")
        self.setCentralWidget(self._loader)
        self._serviceHub.connect("localhost", 11000, b"sixteen byte key")

    def _onSettingsMenuItemClicked(self):
        print("SETTINGS TODO")

    def _onExitMenuItemClicked(self):
        self.hide()
        self.stop()
        QCoreApplication.instance().quit()

    def _isFirstStart(self):
        return False
