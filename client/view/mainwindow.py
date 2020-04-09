import logging
from uuid import uuid4

from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox
from PyQt5.QtCore import Qt, QSettings, QCoreApplication, QSize, pyqtSlot, QThread
from PyQt5.QtGui import QIcon

from model.networkevents import ConnectionEvent, ConnectionEventTypes
from model.config import FirstStartConfig
from model.message import MessageTypes, NetworkMessage
from model.permission import InvalidWorkspacePermissionException

from services.hub import ServiceHub

from view.infopanels import ConnectionErrorPanel
from view.loaders import LoaderWidget
from view.firststart.wizard import FirstStartWizard
from view.mainpanel import MainPanel
from view.settings import SettingsDialog

from . import resources


class MainWindow(QMainWindow):
    __FIRST_START_SIZE = QSize(1280, 720)
    __NORMAL_SIZE = QSize(480, 720)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__loader = LoaderWidget(480, 720, "Connecting to server")
        self.__errorPanel = None
        self.__mainPanel = None
        self.__settingsDialog = SettingsDialog()
        self.__errorDialog = None

        self.__settings = QSettings()
        self.__serviceHub = ServiceHub()
        self.__logger = logging.getLogger(__name__).getChild("MainWindow")

    def initGUI(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background:#FFFFFF")
        self.setWindowTitle('CryptStorePi')
        self.setWindowIcon(QIcon(':logo.png'))
        if self.__isFirstStart():
            self.__logger.debug("Setting up for first start.")
            self.__setupForFirstStart()
            self.show()
        else:
            self.__setupForRegularView()
            self.show()
            self.__normalStartupSequence()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def stop(self):
        self.__serviceHub.shutdownAllServices()

    def __normalStartupSequence(self):
        self.setCentralWidget(self.__loader)
        self.__serviceHub.networkStatusChannel.connect(self.__onNetworkStatusChanged)
        self.__serviceHub.setNetworkInformation(self.__settings.value("server/address"), int(self.__settings.value("server/port")), self.__settings.value("server/encryptionKey"))
        self.__serviceHub.startNetworkService()
        self.__serviceHub.connectToServer()

    def __firstStartStartupSequence(self, config):
        self.__mainPanel.finished.disconnect(self.__onFirstStartFinished)
        self.__firstStartAccounts = config.accounts
        self.__loader.setStatusText("Saving settings")
        self.__setupForRegularView()
        self.setCentralWidget(self.__loader)
        self.repaint()

        self.__saveFirstStartSettings(config)

        self.__loader.setStatusText("Connecting")
        self.__serviceHub.networkStatusChannel.connect(self.__onFirstStartNetworkConnectionChanged)
        self.__serviceHub.setNetworkInformation(self.__settings.value("server/address"), int(self.__settings.value("server/port")), self.__settings.value("server/encryptionKey"))

        self.__serviceHub.connectToServer()

    def __saveFirstStartSettings(self, config):
        self.__settings.setValue("firstStart/isFirstStart", False)
        self.__settings.setValue("server/address", config.network.remote.address)
        self.__settings.setValue("server/port", config.network.remote.port)
        self.__settings.setValue("server/encryptionKey", config.network.remote.encryptionKey.encode())

        self.__settings.setValue("ssh/username", config.network.ssh.username)
        self.__settings.setValue("ssh/password", config.network.ssh.password)

        self.__settings.setValue("syncDir/path", config.network.syncDir)

    def __onFirstStartAccountsSaved(self, _):
        self.__loader.setStatusText("Accounts saved!")
        del self.__firstStartAccounts

        self.__serviceHub.initFileSyncService()

        self.__mainPanel = MainPanel()
        self.__mainPanel.ready.connect(self.__onMainPanelReady)
        self.__mainPanel.syncFileList()

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

    def __isFirstStart(self):
        isFirstStart = self.__settings.value("firstStart/isFirstStart")

        return True if isFirstStart is None or isFirstStart == "true" else False

    @pyqtSlot(ConnectionEvent)
    def __onNetworkStatusChanged(self, event):
        if event.eventType == ConnectionEventTypes.NETWORK_CONNECTED:
            self.__loader.setStatusText("Connected, retrieving session key")
        elif event.eventType == ConnectionEventTypes.NETWORK_HANDSHAKE_SUCCESSFUL:
            self.__loader.setStatusText("Synchronizing file list,\nplease wait!")
            self.__mainPanel = MainPanel()
            self.__mainPanel.ready.connect(self.__onMainPanelReady)
            self.__mainPanel.syncFileList()
        elif event.eventType == ConnectionEventTypes.NETWORK_CONNECTION_ERROR:
            self.__errorPanel = self.__createErrorPanel()
            self.setCentralWidget(self.__errorPanel)

    @pyqtSlot(ConnectionEvent)
    def __onSSHStatusChanged(self, event):
        if event.eventType == ConnectionEventTypes.SSH_CONNECTED:
            self.__loader.setStatusText("Cleaning remote workspace")
            message = NetworkMessage.Builder(MessageTypes.GET_WORKSPACE).withRandomUUID().build()
            self.__serviceHub.sendNetworkMessage(message, self.__onWorkspaceRetrieved)

    def __onWorkspaceRetrieved(self, response):
        try:
            self.__serviceHub.cleanRemoteSSHWorkspace(response['workspace'])
            self.__serviceHub.startFileSyncerService()
            self.setCentralWidget(self.__mainPanel)
            self.repaint()
        except InvalidWorkspacePermissionException as e:
            errorDialog = QMessageBox(self)
            errorDialog.setIcon(QMessageBox.Critical)
            errorDialog.setWindowTitle("Critical error")
            errorDialog.setText(str(e))
            errorDialog.buttonClicked.connect(self.__exitApplication)
            errorDialog.show()

    @pyqtSlot()
    def __onErrorPanelRetryClicked(self):
        self.__loader = LoaderWidget(480, 720, "Connecting to server")
        self.setCentralWidget(self.__loader)
        self.__serviceHub.setNetworkInformation(self.__settings.value("server/address"), int(self.__settings.value("server/port")), self.__settings.value("server/encryptionKey"))
        self.__serviceHub.connectToServer()

    @pyqtSlot()
    def __onSettingsMenuItemClicked(self):
        self.__settingsDialog.show()

    @pyqtSlot()
    def __onExitMenuItemClicked(self):
        self.__exitApplication()

    def __exitApplication(self):
        self.hide()
        self.stop()
        QCoreApplication.instance().quit()

    @pyqtSlot(FirstStartConfig)
    def __onFirstStartFinished(self, config):
        self.__firstStartStartupSequence(config)

    @pyqtSlot(ConnectionEvent)
    def __onFirstStartNetworkConnectionChanged(self, event):
        if event.eventType == ConnectionEventTypes.NETWORK_CONNECTED:
            self.__loader.setStatusText("Connected, retrieving session key")
        elif event.eventType == ConnectionEventTypes.NETWORK_HANDSHAKE_SUCCESSFUL:
            self.__loader.setStatusText("Handshake successful")
            self.__serviceHub.networkStatusChannel.disconnect(self.__onFirstStartNetworkConnectionChanged)
            # TODO ha közben DC valahol, akkor kezeljük.
            self.__firstStartSetupAccounts()

    def __firstStartSetupAccounts(self):
        self.__loader.setStatusText("Updating accounts")
        data = {"accounts": [acc.serialize() for acc in self.__firstStartAccounts]}
        message = NetworkMessage.Builder(MessageTypes.SET_ACCOUNT_LIST).withRandomUUID().withData(data).build()

        self.__serviceHub.sendNetworkMessage(message, self.__onFirstStartAccountsSaved)

    @pyqtSlot()
    def __onMainPanelReady(self):
        self.__loader.setStatusText("Starting SSH service")
        self.__serviceHub.setSSHInformation(self.__settings.value("server/address"), self.__settings.value("ssh/username"), self.__settings.value("ssh/password"))
        self.__serviceHub.sshStatusChannel.connect(self.__onSSHStatusChanged)
        self.__serviceHub.startSshService()
        self.__serviceHub.connectToSSH()
