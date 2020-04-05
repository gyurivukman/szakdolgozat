import logging
from uuid import uuid4

from PyQt5.QtWidgets import QMainWindow, QAction
from PyQt5.QtCore import Qt, QSettings, QCoreApplication, QSize, pyqtSlot
from PyQt5.QtGui import QIcon

from model.events import ConnectionEvent, ConnectionEventTypes
from model.config import FirstStartConfig
from model.message import MessageTypes, NetworkMessage

from services.hub import ServiceHub

from view.infopanels import ConnectionErrorPanel
from view.loaders import LoaderWidget
from view.firststart.wizard import FirstStartWizard
from view.mainpanel import MainPanel

from . import resources


class MainWindow(QMainWindow):
    __FIRST_START_SIZE = QSize(1280, 720)
    __NORMAL_SIZE = QSize(480, 720)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__loader = LoaderWidget(480, 720, "Connecting to server")
        self.__errorPanel = None
        self.__mainPanel = None
        self.__settings = QSettings()
        self.__serviceHub = ServiceHub()
        self.__logger = logging.getLogger(__name__).getChild("MainWindow")

        self.__errorDialog = None

    def initGUI(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background:#FFFFFF")
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QIcon(':logo.png'))
        if self.__isFirstStart():
            self.__logger.debug("Setting up for first start.")
            self.__setupForFirstStart()
        else:
            self.__setupForRegularView()
            self.__mainPanel = MainPanel()
            self.setCentralWidget(self.__mainPanel)
            self.__serviceHub.networkStatusChannel.connect(self.__onNetworkStatusChanged)
            self.__serviceHub.startAllServices()

            self.__serviceHub.setNetworkInformation(self.__settings.value("server/address"), int(self.__settings.value("server/port")), self.__settings.value("server/encryptionKey"))
            self.__serviceHub.setSSHInformation(self.__settings.value("server/address"), str(self.__settings.value("ssh/username")), str(self.__settings.value("ssh/password")))
            self.__serviceHub.connectToServer()
        self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def stop(self):
        self.__serviceHub.shutdownAllServices()

    def __setupForFirstStart(self):
        screenSize = QCoreApplication.instance().desktop().screenGeometry()
        self.setFixedSize(self.__FIRST_START_SIZE)
        self.__moveToCenter(screenSize)
        self.__mainPanel = FirstStartWizard(self)
        self.__mainPanel.finished.connect(self.__onFirstStartFinished)
        self.setCentralWidget(self.__mainPanel)

    def __moveToCenter(self, screenSize):
        posX = (screenSize.width() / 2) - (self.width() / 2)
        posY = (screenSize.height() / 2) - (self.height() / 2)
        self.move(posX, posY)

    def __setupForRegularView(self):
        screenSize = QCoreApplication.instance().desktop().screenGeometry()
        self.__initMenu()
        self.setFixedSize(self.__NORMAL_SIZE)
        self.setCentralWidget(self.__loader)
        self.__moveToCenter(screenSize)

    def __initMenu(self):
        menuBar = self.menuBar()
        menuBar.setStyleSheet("""QMenu:item:selected{background-color: #e36410;}""")
        fileMenu = menuBar.addMenu("File")

        settingsAction = QAction("Settings", self)
        settingsAction.triggered.connect(self.__onSettingsMenuItemClicked)

        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.__onExitMenuItemClicked)
        fileMenu.addAction(settingsAction)
        fileMenu.addAction(exitAction)

    def __createErrorPanel(self):
        panel = ConnectionErrorPanel()
        panel.setFixedSize(480, 720)

        panel.retry.connect(self.__onErrorPanelRetryClicked)

        return panel

    def __onNetworkStatusChanged(self, event):
        if event.eventType == ConnectionEventTypes.NETWORK_CONNECTED:
            self.__loader.setStatusText("Connected, retrieving session key...")
        elif event.eventType == ConnectionEventTypes.NETWORK_HANDSHAKE_SUCCESSFUL:
            self.__loader.setStatusText("Handshake successful\n Starting SSH service...")
            self.__serviceHub.sshStatusChannel.connect(self.__onSSHStatusChanged)
            self.__serviceHub.connectToSSH()
        elif event.eventType == ConnectionEventTypes.NETWORK_CONNECTION_ERROR:
            self.__errorPanel = self.__createErrorPanel()
            self.setCentralWidget(self.__errorPanel)

    def __onSSHStatusChanged(self, event):
        if event.eventType == ConnectionEventTypes.SSH_CONNECTED:
            self.__loader.setStatusText("Retrieving file list,\n please wait!")
            self.__mainPanel = MainPanel()
            self.__mainPanel.ready.connect(self.__onMainPanelReady)
            self.__mainPanel.syncFileList()
        # TODO

    def __onErrorPanelRetryClicked(self):
        # TODO qsettingsbol kiolvasni a connect parametereit, újra és újra minden alkalommal. Ehhez persze kell a config nézet ahol ezt lehet állogatni.
        self.__loader = LoaderWidget(360, 720, "Connecting to server")
        self.setCentralWidget(self.__loader)
        self.__serviceHub.setNetworkInformation("localhost", 11000, b"sixteen byte key")
        self.__serviceHub.connectToServer()

    def __onSettingsMenuItemClicked(self):
        print("SETTINGS TODO")

    def __onExitMenuItemClicked(self):
        self.hide()
        self.stop()
        QCoreApplication.instance().quit()

    def __isFirstStart(self):
        isFirstStart = self.__settings.value("firstStart/isFirstStart")

        return True if isFirstStart is None or isFirstStart == "true" else False
        # return True

    @pyqtSlot(FirstStartConfig)
    def __onFirstStartFinished(self, config):
        self.__mainPanel.finished.disconnect(self.__onFirstStartFinished)
        self.__loader.setStatusText("Saving settings...")
        self.__setupForRegularView()
        self.setCentralWidget(self.__loader)
        self.repaint()

        self.__firstStartConfig = config
        self.__firstStartSaveSettings()
        self.__loader.setStatusText("Starting services...")
        self.__startNetworkServices()

    def __firstStartSaveSettings(self):
        self.__settings.setValue("firstStart/isFirstStart", False)
        self.__settings.setValue("server/address", self.__firstStartConfig.network.remote.address)
        self.__settings.setValue("server/port", self.__firstStartConfig.network.remote.port)
        self.__settings.setValue("server/encryptionKey", self.__firstStartConfig.network.remote.encryptionKey.encode())

        self.__settings.setValue("ssh/username", self.__firstStartConfig.network.ssh.username)
        self.__settings.setValue("ssh/password", self.__firstStartConfig.network.ssh.password)

        self.__settings.setValue("syncDir/path", self.__firstStartConfig.network.syncDir)

    def __startNetworkServices(self):
        self.__serviceHub.initSshService()
        self.__serviceHub.startSshService()

        self.__serviceHub.networkStatusChannel.connect(self.__onFirstStartNetworkConnectionChanged)

        self.__serviceHub.setNetworkInformation(self.__firstStartConfig.network.remote.address, int(self.__firstStartConfig.network.remote.port), self.__firstStartConfig.network.remote.encryptionKey.encode())
        self.__serviceHub.setSSHInformation(self.__firstStartConfig.network.remote.address, self.__firstStartConfig.network.ssh.username, self.__firstStartConfig.network.ssh.password)

        self.__serviceHub.connectToServer()

    @pyqtSlot(ConnectionEvent)
    def __onFirstStartNetworkConnectionChanged(self, event):
        if event.eventType == ConnectionEventTypes.NETWORK_CONNECTED:
            self.__loader.setStatusText("Connected, retrieving session key...")
        elif event.eventType == ConnectionEventTypes.NETWORK_HANDSHAKE_SUCCESSFUL:
            self.__loader.setStatusText("Handshake successful")
            self.__serviceHub.networkStatusChannel.disconnect(self.__onFirstStartNetworkConnectionChanged)
            # TODO ha közben DC valahol, akkor kezeljük.
            self.__firstStartSetupAccounts()

    def __firstStartSetupAccounts(self):
        self.__loader.setStatusText("Updating accounts")

        raw = {"header": {"messageType": MessageTypes.SET_ACCOUNT_LIST, "uuid": uuid4().hex}, "data": {"accounts": [acc.serialize() for acc in self.__firstStartConfig.accounts]}}
        self.__logger.debug(f"\n\n Sending account setup message with accounts: {[acc.serialize() for acc in self.__firstStartConfig.accounts]}\n")
        message = NetworkMessage(raw)

        self.__serviceHub.sendNetworkMessage(message)
        self.__loader.setStatusText("Accounts updated!\nConnecting to SSH...")
        self.__serviceHub.sshStatusChannel.connect(self.__onFirstStartSSHConnectionChanged)
        self.__serviceHub.connectToSSH()

    @pyqtSlot(ConnectionEvent)
    def __onFirstStartSSHConnectionChanged(self, event):
        if event.eventType == ConnectionEventTypes.SSH_CONNECTED:
            self.__loader.setStatusText("Synchronizing file list,\nplease wait!")
            self.__serviceHub.sshStatusChannel.disconnect(self.__onFirstStartSSHConnectionChanged)
            self.__mainPanel = MainPanel()
            self.__mainPanel.ready.connect(self.__onMainPanelReady)
            self.__mainPanel.syncFileList()

    @pyqtSlot()
    def __onMainPanelReady(self, event):
        self.setCentralWidget(self.__mainPanel)
        self.repaint()
