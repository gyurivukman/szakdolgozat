import os, re, json


from os.path import expanduser
from socket import gaierror
from enum import IntEnum
from uuid import uuid4

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDialog,
    QHBoxLayout, QPushButton, QLineEdit,
    QRadioButton, QFileDialog, QScrollArea,
    QCheckBox
)

from view.help import DropboxHelpPage, DriveHelpPage

from PyQt5.QtCore import QSettings, Qt, pyqtSignal, pyqtSlot, QRect, QSize
from PyQt5.QtGui import QColor, QPainter, QFont, QPen, QPixmap, QFontMetrics, QIcon, QIntValidator

from model.config import AccountData, AccountTypes, AccountListChangeEvent  # TODO Rename/refactor
from model.events import ConnectionEventTypes, ConnectionEvent
from model.message import NetworkMessage, MessageTypes
from services.hub import ServiceHub
from view.loaders import LoaderWidget
from view import resources


class AccountHelpDialog(QDialog):

    def __init__(self, *args, **kwargs):
        scrollWidget = kwargs.pop('scrollWidget')
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("self")
        self.setStyleSheet(
            """
                QDialog#self, QScrollArea{background-color:white; border:none;}
                QPushButton#closeHelpButton{
                    background-color:#e36410;
                    color:white;
                    width:150px;
                    border:0px;
                    height:30px;
                    margin-right:5px;
                }
                QPushButton#closeHelpButton:pressed {background-color:#e68a4e;}
            """
        )
        self.setFixedSize(600, 720)
        self._setup(scrollWidget)

    def _setup(self, scrollWidget):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setFixedHeight(680)
        scroll.setAttribute(Qt.WA_StyledBackground)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(False)

        scroll.setWidget(scrollWidget)

        controlLayout = QHBoxLayout()
        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.hide)
        closeButton.setObjectName("closeHelpButton")
        controlLayout.setAlignment(Qt.AlignRight)
        controlLayout.addWidget(closeButton)

        layout.addWidget(scroll)
        layout.addLayout(controlLayout)
        layout.addStretch(1)
        self.setLayout(layout)


class FirstStartWizard(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__settings = QSettings()
        self.__widgetMap = self.__createWidgetMap()
        self.__setup()

    def __createWidgetMap(self):
        widgetMap = {
            WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME: WelcomeWidget()
        }

        setupNetworkWidget = SetupNetworkWidget()
        setupNetworkWidget.formValidityChanged.connect(self.__checkCanProceed)
        widgetMap[WizardProgressWidget.WIZARD_PROGRESS_STATES.NETWORK] = setupNetworkWidget

        setupAccountsWidget = SetupAccountsWrapperWidget()
        setupAccountsWidget.formValidityChanged.connect(self.__checkCanProceed)
        widgetMap[WizardProgressWidget.WIZARD_PROGRESS_STATES.ACCOUNTS] = setupAccountsWidget

        summaryWidget = FirstStartSummaryWidget()
        widgetMap[WizardProgressWidget.WIZARD_PROGRESS_STATES.SUMMARY] = summaryWidget

        return widgetMap

    def __checkCanProceed(self):
        self.__nextButton.setDisabled(not self.__widgetMap[self.__state].canProceed())

    def __setup(self):
        self.__state = WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME
        self.__setupStyle()
        self.__setupWidgets()

    def __setupStyle(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(
            """
                QPushButton#controlButton {
                    background-color:#e36410;
                    color:white;
                    width:150px;
                    border:0px;
                    height:30px;
                }

                QPushButton#controlButton:disabled {
                    background-color:#D8D8D8;
                }

                QPushButton#controlButton:pressed {
                    background-color:#e68a4e;
                }
            """
        )

    def __setupWidgets(self):
        self.__layout = QVBoxLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(0)
        self.__progressWidget = WizardProgressWidget()
        self.__layout.addWidget(self.__progressWidget, 0, Qt.AlignTop)

        for key, widget in self.__widgetMap.items():
            self.__layout.addWidget(widget, 0, Qt.AlignTop)
            widget.show() if key == WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME else widget.hide()
        self.__layout.addStretch(1)

        self.__nextButton = QPushButton("Next")
        self.__nextButton.clicked.connect(self.__goNext)
        self.__nextButton.setObjectName("controlButton")
        self.__previousButton = QPushButton("Back")
        self.__previousButton.setObjectName("controlButton")
        self.__previousButton.setDisabled(True)
        self.__previousButton.clicked.connect(self.__goBack)
        self.__finishButton = QPushButton("Finish")
        self.__finishButton.setObjectName("controlButton")
        self.__finishButton.clicked.connect(self.__onFinishClicked)
        self.__finishButton.hide()

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 10, 10)
        controlLayout.setSpacing(20)
        controlLayout.setAlignment(Qt.AlignTrailing)
        controlLayout.addWidget(self.__previousButton)
        controlLayout.addWidget(self.__nextButton)
        controlLayout.addWidget(self.__finishButton)

        self.__layout.addLayout(controlLayout)
        self.setLayout(self.__layout)

    def __goNext(self):
        self.__widgetMap[self.__state].hide()
        self.__state = self.__progressWidget.toNextState()
        self.__widgetMap[self.__state].show()
        if self.__state != WizardProgressWidget.WIZARD_PROGRESS_STATES.SUMMARY:
            self.__widgetMap[self.__state].initData()
        else:
            self.__widgetMap[self.__state].setSummaryData(self.__gatherFormData())
        self.__update()

    def __goBack(self):
        self.__widgetMap[self.__state].hide()
        self.__state = self.__progressWidget.toPreviousState()
        self.__widgetMap[self.__state].show()
        self.__update()

    def __gatherFormData(self):
        networkData = self.__widgetMap[WizardProgressWidget.WIZARD_PROGRESS_STATES.NETWORK].getFormData()
        accountsData = self.__widgetMap[WizardProgressWidget.WIZARD_PROGRESS_STATES.ACCOUNTS].getFormData()

        return {'network': networkData, 'accounts': accountsData}

    def __onFinishClicked(self):
        print("Finish!")

    def __update(self):
        if self.__state != WizardProgressWidget.WIZARD_PROGRESS_STATES.SUMMARY:
            self.__nextButton.show()
            self.__nextButton.setDisabled(not self.__widgetMap[self.__state].canProceed())
            self.__finishButton.hide()
        else:
            self.__nextButton.hide()
            self.__finishButton.show()
        self.__previousButton.setDisabled(not self.__widgetMap[self.__state].canGoBack())
        self.__progressWidget.update()
        self.update()


class WizardProgressWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__state = WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME
        self.__activeStateColor = QColor('#E39910')
        self.__inactiveStateColor = QColor('#D8D8D8')
        self.__separatorLineColor = QColor('#777777')
        self.__stageIndexFont = QFont('Arial', 32, QFont.Bold, False)
        self.__stageLabelFont = QFont('Arial', 10, QFont.Bold, False)
        self.setFixedSize(1280, 160)

    def paintEvent(self, _):
        qp = QPainter()
        qp.begin(self)
        self.__drawWidget(qp)
        qp.end()

    def __drawWidget(self, painter):
        self.__drawProgressIcons(painter)
        self.__drawSeparatorLine(painter)

    def __drawProgressIcons(self, painter):
        pen = QPen(self.__activeStateColor, 6, Qt.SolidLine)
        for state in self.WIZARD_PROGRESS_STATES:
            posX = (state.value * 320) + 120
            posY = 15
            width = 80
            height = 80
            if state <= self.__state:
                pen.setColor(self.__activeStateColor)
            else:
                pen.setColor(self.__inactiveStateColor)
            painter.setPen(pen)
            painter.setFont(self.__stageIndexFont)
            painter.drawRect(posX, posY, width, height)
            painter.drawText(QRect(posX, posY, width, height), Qt.AlignCenter, str(state.value + 1))
            painter.setFont(self.__stageLabelFont)
            painter.drawText(QRect(posX, posY + 90, width, 30), Qt.AlignCenter, state.toDisplayValue())
            if state > self.WIZARD_PROGRESS_STATES.WELCOME:
                painter.drawLine(posX - 6, posY + (height / 2), posX - 234, posY + (height / 2))

    def __drawSeparatorLine(self, painter):
        pen = QPen(self.__inactiveStateColor, 1, Qt.SolidLine)
        painter.setPen(pen)
        painter.drawLine(10, 159, 1270, 159)

    def toNextState(self):
        self.__state = self.__state.next()
        return self.__state

    def toPreviousState(self):
        self.__state = self.__state.previous()
        return self.__state

    class WIZARD_PROGRESS_STATES(IntEnum):
        WELCOME = 0
        NETWORK = 1
        ACCOUNTS = 2
        SUMMARY = 3

        def next(self):
            if self.value == 3:
                raise ValueError('Enumeration ended')
            return WizardProgressWidget.WIZARD_PROGRESS_STATES(self.value + 1)

        def previous(self):
            if self.value == 0:
                raise ValueError('Enumeration ended')
            return WizardProgressWidget.WIZARD_PROGRESS_STATES(self.value - 1)

        def toDisplayValue(self):
            ENUM_DISPLAY_VALUES = ['Welcome', 'Network &\nDirectory', 'Accounts', 'Summary']
            return ENUM_DISPLAY_VALUES[self.value]


class FirstStartWizardMiddleWidget(QWidget):

    formValidityChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serviceHub = ServiceHub.getInstance()
        self.setFixedSize(1280, 480)
        self.__setupStylesheet()
        self._setup()

    def __setupStylesheet(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(self._getStyle())

    def _setup(self):
        raise NotImplementedError('Derived class must implement method "_setup"')

    def _getStyle(self):
        raise NotImplementedError('Derived class must implement method "_getStyle". It should return a valid qss stylesheet string.')

    def canProceed(self):
        raise NotImplementedError('Derived class must implement method "canProceed". It should return a bool.')

    def canGoBack(self):
        raise NotImplementedError('Derived class must implement method "canGoBack" it should return a bool.')

    def initData(self):
        pass


class WelcomeWidget(FirstStartWizardMiddleWidget):

    def _setup(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 50, 0, 0)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignTop)

        welcomeLabel = QLabel("Welcome to CryptStorePi!")
        welcomeLabel.setAttribute(Qt.WA_TranslucentBackground)
        welcomeLabelFont = QFont('Nimbus Sans L', 42, QFont.Normal)
        welcomeLabel.setFont(welcomeLabelFont)

        welcomeInstructionsLabel = QLabel("This wizard will guide you through the first setup of this application.")
        welcomeInstructionsLabel.setFont(QFont('Nimbus Sans L', 18, QFont.Normal))
        welcomeInstructionsLabel.setAttribute(Qt.WA_TranslucentBackground)
        continueInstructionLabel = QLabel("To start, click 'Next'!")
        continueInstructionLabel.setFont(QFont('Nimbus Sans L', 16, QFont.Normal))
        continueInstructionLabel.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(welcomeLabel, 0, Qt.AlignHCenter | Qt.AlignTop)
        layout.addWidget(welcomeInstructionsLabel, 0, Qt.AlignHCenter)
        layout.addWidget(continueInstructionLabel, 0, Qt.AlignHCenter)
        self.setLayout(layout)

    def canProceed(self):
        return True

    def canGoBack(self):
        return False

    def _getStyle(self):
        self.setObjectName("welcomeWidget")
        return "#welcomeWidget{background-image:url(:encryptionBackground.png);background-repeat:no-repeat;background-position:center;}"


class SetupNetworkWidget(FirstStartWizardMiddleWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__chosenDirectoryPath = None

    def canProceed(self):
        return self.__isConnectionOK and self.__isSshOK and self.__chosenDirectoryPath is not None

    def canGoBack(self):
        return True

    def getFormData(self):
        return {
            "remote": {
                "address": self.__remoteHostNameInput.text(),
                "port": self.__remotePortInput.text(),
                "encryptionKey": self.__aesKeyInput.text()
            },
            "ssh": {
                "username": None,
                "password": None
            },
            "syncDir": self.__chosenDirectoryPath
        }

    def _getStyle(self):
        return """
            QLineEdit {border:1px solid #E39910; height:25px;}
            QLineEdit:focus {border:2px solid #E39910}
            QLineEdit:hover {border:2px solid #E39910}

            QPushButton {width: 150px; max-width:150px; height:25px; border:0; margin-right:20px; background-color:#e36410; color:white;}
            QPushButton#chooseSyncDir{height:27px; width:80px;max-width:80px;margin-right:40px;}
            QPushButton:pressed {background-color:#e68a4e;}

            QLineEdit#hostName, QLineEdit#syncDirectory {max-width: 500px; margin-right:20px;}
            QLineEdit#hostPort {max-width: 80px; margin-right:40px;}
            QLineEdit#aesKey {max-width: 602px; margin-right:40px;}

            QLineEdit#sshUsername {max-width: 290px; margin-right:20px;}
            QLineEdit#sshPassword {max-width: 290px; margin-right:40px;}
            QLineEdit#syncDirectory {border:1px solid #D8D8D8;}
        """

    def _setup(self):
        self.__formLabelFont = QFont("Nimbus Sans L", 13)
        self.__descriptionFont = QFont("Nimbus Sans L", 10)
        self.__formInputFont = QFont("Nimbus Sans L", 11)

        self.__isConnectionOK = False
        self.__isSshOK = False

        layout = QVBoxLayout()

        hostLayout = self.__createHostLayout()
        sshLayout = self.__createSSHLayout()
        directoryLayout = self.__createSyncDirectoryLayout()

        layout.addLayout(hostLayout)
        layout.addLayout(sshLayout)
        layout.addLayout(directoryLayout)
        layout.setAlignment(Qt.AlignHCenter)
        layout.setContentsMargins(100, 50, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)

        self.setLayout(layout)

    def __createHostLayout(self):
        #TODO Refactor + Input validation!
        hostLayout = QVBoxLayout()

        hostFormLayout = QHBoxLayout()
        remoteHostNameInputLayout = QVBoxLayout()
        remoteHostPortInputLayout = QVBoxLayout()
        remoteHostTestLayout = QHBoxLayout()
        aesKeyFormLayout = QHBoxLayout()
        aesKeyInputLayout = QVBoxLayout()

        remoteHostNameLabel = QLabel("Remote host")
        remoteHostNameLabel.setFont(self.__formLabelFont)
        remoteHostDescription = QLabel("Resolveable address of the remote CryptStorePi server.\nExamples address: localhost or 10.20.30.40\nExample port: 12345")
        remoteHostDescription.setFont(self.__descriptionFont)
        remoteHostDescription.setAlignment(Qt.AlignBottom)

        self.__remoteHostNameInput = QLineEdit()
        self.__remoteHostNameInput.setObjectName("hostName")
        self.__remoteHostNameInput.setFont(QFont("Nimbus Sans L", 12))
        self.__remoteHostNameInput.textChanged.connect(self.__onFormInputChanged)
        remoteHostNameInputLayout.addWidget(remoteHostNameLabel)
        remoteHostNameInputLayout.addWidget(self.__remoteHostNameInput)

        remoteHostPortLabel = QLabel("Port")
        remoteHostPortLabel.setFont(self.__formLabelFont)
        self.__remotePortInput = QLineEdit()
        self.__remotePortInput.setObjectName("hostPort")
        self.__remotePortInput.setFont(self.__formInputFont)
        self.__remotePortInput.setValidator(QIntValidator(0, 65535))
        self.__remotePortInput.textChanged.connect(self.__onFormInputChanged)
        remoteHostPortInputLayout.addWidget(remoteHostPortLabel)
        remoteHostPortInputLayout.addWidget(self.__remotePortInput)

        hostFormLayout.addLayout(remoteHostNameInputLayout)
        hostFormLayout.addLayout(remoteHostPortInputLayout)
        hostFormLayout.addWidget(remoteHostDescription)
        hostFormLayout.setContentsMargins(0, 0, 0, 0)
        hostFormLayout.setAlignment(Qt.AlignHCenter)

        self.__remoteHostTestResultLabel = QLabel()
        self.__remoteHostTestResultLabel.setObjectName("connectionTestText")
        self.__remoteHostTestResultLabel.setFont(self.__formInputFont)

        aesKeyInputLabel = QLabel("Network encryption key")
        aesKeyInputLabel.setFont(self.__formLabelFont)

        self.__aesKeyInput = QLineEdit()
        self.__aesKeyInput.setObjectName("aesKey")
        self.__aesKeyInput.setFont(self.__formInputFont)
        self.__aesKeyInput.setMaxLength(16)
        self.__aesKeyInput.textChanged.connect(self.__onFormInputChanged)

        aesKeyInputLayout.addWidget(aesKeyInputLabel)
        aesKeyInputLayout.addWidget(self.__aesKeyInput)

        aesKeyDescription = QLabel("16 byte AESKey. Example: IAmAProperAesKey")
        aesKeyDescription.setFont(self.__descriptionFont)

        aesKeyFormLayout.addLayout(aesKeyInputLayout)
        aesKeyFormLayout.addWidget(aesKeyDescription)

        testRemoteHostButton = QPushButton("Test Connection")
        testRemoteHostButton.setObjectName("testConnection")
        testRemoteHostButton.clicked.connect(self.__testConnection)

        remoteHostTestLayout.addWidget(testRemoteHostButton)
        remoteHostTestLayout.addWidget(self.__remoteHostTestResultLabel)
        remoteHostTestLayout.setContentsMargins(0, 5, 0, 0)
        remoteHostTestLayout.setAlignment(Qt.AlignLeft)

        hostLayout.addLayout(hostFormLayout)
        hostLayout.addSpacing(10)
        hostLayout.addLayout(aesKeyFormLayout)
        hostLayout.addLayout(remoteHostTestLayout)
        hostLayout.setAlignment(Qt.AlignHCenter)

        return hostLayout

    def __createSSHLayout(self):
        sshLayout = QVBoxLayout()
        sshFormLayout = QHBoxLayout()
        sshFormUsernameInputLayout = QVBoxLayout()
        sshFormPasswordInputLayout = QVBoxLayout()
        sshFormTestConnectionLayout = QHBoxLayout()

        sshUsernameLabel = QLabel("SSH Username")
        sshUsernameLabel.setFont(self.__formLabelFont)
        self.__sshUsernameInput = QLineEdit()
        self.__sshUsernameInput.setObjectName("sshUsername")
        self.__sshUsernameInput.setFont(self.__formInputFont)
        self.__sshUsernameInput.textChanged.connect(self.__onFormInputChanged)
        sshFormUsernameInputLayout.addWidget(sshUsernameLabel)
        sshFormUsernameInputLayout.addWidget(self.__sshUsernameInput)

        sshPasswordLabel = QLabel("SSH Password")
        sshPasswordLabel.setFont(self.__formLabelFont)
        sshPasswordLabel.setMaximumWidth(150)
        showPasswordCheckbox = QCheckBox("Show")
        showPasswordCheckbox.setMaximumWidth(57)
        showPasswordCheckbox.stateChanged.connect(self.__checkboxStateChanged)

        sshPasswordLabelsLayout = QHBoxLayout()
        sshPasswordLabelsLayout.setAlignment(Qt.AlignLeading)
        sshPasswordLabelsLayout.setSizeConstraint(QHBoxLayout.SetMaximumSize)
        sshPasswordLabelsLayout.addWidget(sshPasswordLabel)
        sshPasswordLabelsLayout.addSpacing(120)
        sshPasswordLabelsLayout.addWidget(showPasswordCheckbox)

        self.__sshPasswordInput = QLineEdit()
        self.__sshPasswordInput.setObjectName("sshPassword")
        self.__sshPasswordInput.setFont(self.__formInputFont)
        self.__sshPasswordInput.setEchoMode(QLineEdit.Password)
        self.__sshPasswordInput.textChanged.connect(self.__onFormInputChanged)

        sshFormPasswordInputLayout.addLayout(sshPasswordLabelsLayout)
        sshFormPasswordInputLayout.addWidget(self.__sshPasswordInput)

        self.__SSHTestResultLabel = QLabel()
        self.__SSHTestResultLabel.setObjectName("sshTestText")
        self.__SSHTestResultLabel.setFont(self.__formInputFont)

        testSSHButton = QPushButton("Test SSH")
        testSSHButton.setObjectName("testSSH")
        testSSHButton.clicked.connect(self.__test_ssh_connection)
        sshFormTestConnectionLayout.addWidget(testSSHButton)
        sshFormTestConnectionLayout.addWidget(self.__SSHTestResultLabel)
        sshFormTestConnectionLayout.setContentsMargins(0, 5, 0, 0)
        sshFormTestConnectionLayout.setAlignment(Qt.AlignLeft)

        sshFormLayout.addLayout(sshFormUsernameInputLayout)
        sshFormLayout.addLayout(sshFormPasswordInputLayout)
        sshFormLayout.setAlignment(Qt.AlignLeft)

        sshDescriptionLabel = QLabel("SSH Username and password.\nCryptStorePi uses SSH to upload and download your files to and from\nthe CryptStorePi encryption server.")
        sshDescriptionLabel.setFont(self.__descriptionFont)
        sshDescriptionLabel.setAlignment(Qt.AlignBottom)
        sshFormLayout.addWidget(sshDescriptionLabel)

        sshLayout.addLayout(sshFormLayout)
        sshLayout.addLayout(sshFormTestConnectionLayout)
        sshLayout.setContentsMargins(0, 25, 0, 0)
        return sshLayout

    def __createSyncDirectoryLayout(self):
        directoryLayout = QHBoxLayout()
        directoryFormLayout = QVBoxLayout()
        chooseButtonLayout = QVBoxLayout()

        syncDirLabel = QLabel("Synchronization directory")
        syncDirLabel.setFont(self.__formLabelFont)

        syncDirDescription = QLabel("Choose a directory, which will be used to synchronize with the cloud services.")
        syncDirDescription.setFont(self.__descriptionFont)
        syncDirDescription.setAlignment(Qt.AlignBottom)

        self.__syncDirInput = QLineEdit()
        self.__syncDirInput.setObjectName("syncDirectory")
        self.__syncDirInput.setFont(QFont("Nimbus Sans L", 12))
        self.__syncDirInput.setEnabled(False)

        chooseSyncDirButton = QPushButton("Choose")
        chooseSyncDirButton.setObjectName("chooseSyncDir")
        chooseSyncDirButton.clicked.connect(self.__openDirectoryBrowser)

        directoryFormLayout.setContentsMargins(0, 0, 0, 0)
        directoryFormLayout.addWidget(syncDirLabel)
        directoryFormLayout.addWidget(self.__syncDirInput)

        chooseButtonLayout.addStretch(1)
        chooseButtonLayout.addWidget(chooseSyncDirButton)

        directoryLayout.addLayout(directoryFormLayout)
        directoryLayout.addLayout(chooseButtonLayout)
        directoryLayout.addWidget(syncDirDescription)
        directoryLayout.setContentsMargins(0, 25, 0, 0)

        return directoryLayout

    def __testConnection(self):
        self._serviceHub.networkStatusChannel.connect(self.__on_network_event)
        address = self.__remoteHostNameInput.text()
        port = self.__remotePortInput.text()
        aesKey = self.__aesKeyInput.text()

        try:
            self._serviceHub.setNetworkInformation(address, int(port), aesKey.encode())
            self._serviceHub.connect()
        except (ConnectionError, gaierror):
            self.__connectionTestFailed("Couldn't connect to the specified remote.")

    def __connectionTestSuccessful(self):
        self.__remoteHostTestResultLabel.setStyleSheet("color:green;")
        self.__remoteHostTestResultLabel.setText("OK")
        self.__isConnectionOK = True
        self._serviceHub.networkStatusChannel.disconnect(self.__on_network_event)
        self.formValidityChanged.emit()

    def __connectionTestFailed(self, message):
        self.__isConnectionOK = False
        self.__remoteHostTestResultLabel.setStyleSheet("color:red;")
        self.__remoteHostTestResultLabel.setText(message)
        self._serviceHub.networkStatusChannel.disconnect(self.__on_network_event)
        self.formValidityChanged.emit()

    def __on_network_event(self, event):
        if event.eventType == ConnectionEventTypes.HANDSHAKE_SUCCESSFUL:
            self.__connectionTestSuccessful()
            self._serviceHub.disconnect()
        elif event.eventType == ConnectionEventTypes.CONNECTION_ERROR:
            self.__connectionTestFailed(event.data['message'])
            self._serviceHub.disconnect()

    def __test_ssh_connection(self):
        self.__SSHTestResultLabel.setStyleSheet("color:green;")
        self.__SSHTestResultLabel.setText("OK")
        self.__isSshOK = True

        self.formValidityChanged.emit()

    def __openDirectoryBrowser(self):
        self.__chosenDirectoryPath = str(QFileDialog.getExistingDirectory(self, "Select the synchronization directory", expanduser("~"),QFileDialog.ShowDirsOnly))
        self.__syncDirInput.setText(self.__chosenDirectoryPath)
        self.formValidityChanged.emit()

    def __onFormInputChanged(self):
        self.__isSshOK = False
        self.__isConnectionOK = False
        self.__SSHTestResultLabel.setText("")
        self.__remoteHostTestResultLabel.setText("")
        self.formValidityChanged.emit()

    def __checkboxStateChanged(self, state):
        echoMode = QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password
        self.__sshPasswordInput.setEchoMode(echoMode)


class SetupAccountsWrapperWidget(FirstStartWizardMiddleWidget):
    __inited = False
    __canProceed = False

    def canProceed(self):
        return self.__canProceed

    def canGoBack(self):
        return True

    def initData(self):
        if self.__inited is False:
            self.__formData = []
            self._serviceHub.startNetworkService()
            self._serviceHub.connect()
            raw = {"header": {"messageType": MessageTypes.GET_ACCOUNT_LIST, "uuid": uuid4().hex}, "data": None}
            self._serviceHub.sendNetworkMessage(NetworkMessage(raw), self.__onAccountsRetrieved)

    def _getStyle(self):
        return ""

    def _setup(self):
        self.__layout = QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.__loadingWidget = LoaderWidget(1280, 480)
        self.__accountsWidget = SetupAccountsWidget()

        self.__layout.addWidget(self.__loadingWidget)
        self.__layout.addWidget(self.__accountsWidget)
        self.__accountsWidget.hide()
        self.setLayout(self.__layout)

    def __onAccountsRetrieved(self, accounts):
        self.__inited = True
        self.__accountsWidget.setAccountData(accounts)
        self.__loadingWidget.hide()
        self.__accountsWidget.show()

    def __onAccountListChanged(self, event):
        self.formValidityChanged.emit(self.__canProceed)

    def getFormData(self):
        return self.__accountsWidget.getAccounts()


class SetupAccountsWidget(QWidget):
    accountListChanged = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__accountCardWidgets = []
        self.__accountListLayout = None
        self.__selectedAccountIndex = None
        self.__addAccountButton = None

        self.setFixedSize(1280, 480)
        self.setStyleSheet(
            """
                QWidget#noAccountsWidget{border-right:2px solid #777777;}

                QPushButton#addAccountButton{height: 25px; border:1px dashed #e36410;max-width:293px;margin-left:2px;}
                QPushButton#addAccountButton:hover{border:2px dashed #e36410;}
            """
        )
        self.__setup()

    def __setup(self):
        self.__noAccountsWidget = QLabel("No accounts could be found, please create new accounts by clicking the 'Add new account' button on the right hand side. \nYou can have a total of 8 accounts.")
        self.__noAccountsWidget.setFont(QFont("Nimbus Sans L", 13, False))
        self.__noAccountsWidget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.__noAccountsWidget.setObjectName("noAccountsWidget")

        self.__accountEditorWidget = AccountEditorWidget()
        self.__accountEditorWidget.hide()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.__noAccountsWidget)
        layout.addWidget(self.__accountEditorWidget)
        self.__accountListLayout = self.__createEmptyAccountListLayout()
        layout.addLayout(self.__accountListLayout)

        self.setLayout(layout)

    def __createEmptyAccountListLayout(self):
        self.__addAccountButton = QPushButton("Add Account")
        self.__addAccountButton.setFont(QFont("Nimbus Sans L", 10))
        self.__addAccountButton.setObjectName("addAccountButton")
        self.__addAccountButton.clicked.connect(self.__onAddNewAccountClicked)
        self.__addAccountButton.setFocusPolicy(Qt.NoFocus)

        layout = QVBoxLayout()
        layout.addWidget(self.__addAccountButton)
        layout.addStretch(1)
        return layout

    def __addBlankAccount(self):
        blankAccountData = AccountData(AccountTypes.Dropbox, "New Account", "", {"apiToken": ""})
        self.__addAccountWidget(blankAccountData)
        new_account_index = len(self.__accountCardWidgets) - 1
        self.__selectAccount(new_account_index)
        if len(self.__accountCardWidgets) == 8:
            self.__addAccountButton.hide()

    def __addAccountWidget(self, accountData):
        index = self.__accountListLayout.count() - 2  # Button + Spaceritem is there by default.
        accountCard = AccountCard(accountData=accountData, index=index)
        accountCard.onSelected.connect(self.__onAccountCardSelected) # TODO disconnect
        accountCard.removeButtonClicked.connect(self.__onAccountCardRemoveClicked) #TODO disconnect

        self.__accountCardWidgets.append(accountCard)
        self.__accountListLayout.insertWidget(index, accountCard, Qt.AlignHCenter)

    def __selectAccount(self, index):
        if self.__selectedAccountIndex is not None:
            self.__accountCardWidgets[self.__selectedAccountIndex].setSelected(False)
        self.__selectedAccountIndex = index
        self.__accountCardWidgets[index].setSelected(True)
        self.__accountEditorWidget.setAccountData(self.__accountCardWidgets[index].getAccountData())

    def setAccountData(self, accounts):
        accountCount = len(accounts)
        for accountData in accounts:
            self.__addAccountWidget(accountData)

        if accountCount > 0:
            self.__selectAccount(0)
            self.__noAccountsWidget.hide()
            self.__accountEditorWidget.show()

    def __onAccountSaveClicked(self, account):
        # self.__accountListWidget.updateCurrentlySelectedAccount(account)
        # self.accountListChanged.emit(AccountListChangeEvent(AccountListChangeEvent.CREATE_OR_UPDATE, account))
        print("ACCOUNT SAVE CLICKED")

    def __onAccountCardSelected(self, index):
        if self.__selectedAccountIndex is not None:
            self.__accountCardWidgets[self.__selectedAccountIndex].setSelected(False)
        self.__selectAccount(index)

    def __onAccountCardRemoveClicked(self, index):
        self.__accountCardWidgets[index].hide()
        self.__accountListLayout.removeWidget(self.__accountCardWidgets[index])
        del self.__accountCardWidgets[index]
        remainingAccountCount = len(self.__accountCardWidgets)
        if remainingAccountCount < 8:
            self.__addAccountButton.show()

        for i in range(remainingAccountCount):
            self.__accountCardWidgets[i].setIndex(i)

        if remainingAccountCount > 0:
            if index == self.__selectedAccountIndex:
                self.__selectedAccountIndex = None
                self.__selectAccount(remainingAccountCount - 1)
            elif index < self.__selectedAccountIndex:
                self.__selectedAccountIndex = self.__selectedAccountIndex - 1
        else:
            self.__selectedAccountIndex = None
            self.__accountEditorWidget.hide()
            self.__noAccountsWidget.show()

    def __onAddNewAccountClicked(self, _):
        self.__addBlankAccount()
        if not self.__accountEditorWidget.isVisible():
            self.__noAccountsWidget.hide()
            self.__accountEditorWidget.show()

    def getAccounts(self):
        return []


class AccountEditorWidget(QWidget):
    onSaveAccount = pyqtSignal(object)
    onRemoveAccount = pyqtSignal()

    __hasAccountData = False
    __accountTypeButtons = []
    __selectedAccountTypeIndex = 0
    __accountForms = []

    __activeButtonStyle = """
            QPushButton{background-color:#FFFFFF; border:2px solid #e36410; width:350px; max-width:350px; height:60px; font-size:18px;}
            QPushButton:pressed{border:2px solid #e36410;}        
        """
    __inactiveButtonStyle = """
            QPushButton{background-color:#FFFFFF; border:2px solid #777777; width:350px; max-width:350px; height:60px; font-size:18px;}
            QPushButton:pressed{border:2px solid #e36410;}
        """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedSize(960, 480)
        self.__accountForms = self.__createAccountForms()
        self.setObjectName("accountEditor")
        self.setStyleSheet("#accountEditor{border-right:2px solid #777777;}")
        self.__setup()

    def __createAccountForms(self):
        return [DropboxAccountForm(), DriveAccountForm()]

    def __setup(self):
        layout = QVBoxLayout()
        layout.addWidget(AccountEditorSectionSeparatorWidget(sectionName="Account Type"))
        layout.addLayout(self.__createAccountTypeLayout())
        layout.addWidget(AccountEditorSectionSeparatorWidget(sectionName="Credentials"))
        for accountForm, index in zip(self.__accountForms, range(len(self.__accountForms))):
            accountForm.formValidityChanged.connect(self.__onFormValidityChanged)
            layout.addWidget(accountForm)
            if index > 0:
                accountForm.hide()
        layout.addLayout(self.__createAccountEditorControlsLayout())
        layout.addStretch(1)
        self.setLayout(layout)

    def __createAccountTypeLayout(self):
        accountTypeLayout = QHBoxLayout()
        accountTypeLayout.setContentsMargins(0, 15, 0, 15)
        self.__accountTypeButtons = self.__createAccountButtons()
        accountTypeLayout.addWidget(self.__accountTypeButtons[0])
        accountTypeLayout.addWidget(self.__accountTypeButtons[1])

        return accountTypeLayout

    def __createAccountButtons(self):
        accountIconSize = QSize(35, 35)

        dropboxButton = QPushButton("Dropbox")
        dropboxButton.setIcon(QIcon(':/dropbox.png'))
        dropboxButton.setIconSize(accountIconSize)
        dropboxButton.setStyleSheet(self.__activeButtonStyle)
        dropboxButton.clicked.connect(lambda: self.__onAccountTypeSelected(0))

        driveButton = QPushButton("Google Drive")
        driveButton.setIcon(QIcon(':googledrive.png'))
        driveButton.setIconSize(accountIconSize)
        driveButton.setStyleSheet(self.__inactiveButtonStyle)
        driveButton.clicked.connect(lambda: self.__onAccountTypeSelected(1))

        return [dropboxButton, driveButton]

    def __onAccountTypeSelected(self, index):
        if index != self.__selectedAccountTypeIndex:
            self.__updateAccountTypeButtons(index)
            self.__displayNewAccountForm(index)
            self.__selectedAccountTypeIndex = index
            self.__accountForms[index].reset()
            self.__saveAccountButton.setEnabled(self.__accountForms[self.__selectedAccountTypeIndex].isFormValid())

    def __updateAccountTypeButtons(self, index):
        self.__accountTypeButtons[self.__selectedAccountTypeIndex].setStyleSheet(self.__inactiveButtonStyle)
        self.__accountTypeButtons[index].setStyleSheet(self.__activeButtonStyle)

    def __displayNewAccountForm(self, index):
        self.__accountForms[self.__selectedAccountTypeIndex].hide()
        self.__selectedAccountTypeIndex = index
        self.__accountForms[index].show()

    def __createAccountEditorControlsLayout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 50, 0, 0)
        layout.setAlignment(Qt.AlignTrailing)
        self.__saveAccountButton = QPushButton("Save")
        self.__saveAccountButton.setDisabled(True)
        self.__saveAccountButton.setStyleSheet("""
                QPushButton{
                    background-color:#e36410;
                    color:white;
                    width:150px;
                    border:0px;
                    height:30px;
                    margin-top:15px;
                }

                QPushButton:pressed {background-color:#e68a4e;}
                QPushButton:disabled {background-color:#D8D8D8;}
            """
        )
        self.__saveAccountButton.clicked.connect(self.__onAccountSave)
        layout.addWidget(self.__saveAccountButton)

        return layout

    def __onAccountSave(self):
        accountForm = self.__accountForms[self.__selectedAccountTypeIndex]
        self.onSaveAccount.emit(accountForm.getAccountData())

    @pyqtSlot(bool)
    def __onFormValidityChanged(self, value):
        if self.__saveAccountButton.isEnabled() != value:
            self.__saveAccountButton.setDisabled(not value)

    def setAccountData(self, accountData):
        index = 0 if accountData.accountType == AccountTypes.Dropbox else 1
        self.__updateAccountTypeButtons(index)
        self.__displayNewAccountForm(index)
        self.__accountForms[index].setAccountData(accountData)


class AccountEditorSectionSeparatorWidget(QWidget):

    def __init__(self, *args, **kwargs):
        self.__sectionText = kwargs.pop("sectionName")
        self.__sectionFont = QFont(QFont('Nimbus Sans L', 12, QFont.Bold))
        self.__sectionFontColor = QColor("#777777")
        self.__sectionLineColor = QColor("#ECECEC")
        self.__sectionFontMetrics = QFontMetrics(self.__sectionFont)
        super().__init__(*args, **kwargs)
        self.setFixedSize(960, 25)

    def paintEvent(self, _):
        qp = QPainter()
        qp.begin(self)
        self.__drawWidget(qp)
        qp.end()

    def __drawWidget(self, painter):
        width = self.__sectionFontMetrics.width(self.__sectionText)
        height = self.__sectionFontMetrics.height()

        painter.setFont(self.__sectionFont)
        painter.setPen(QPen(self.__sectionFontColor, 1, Qt.SolidLine))
        painter.drawText(QRect(480 - (width / 2), 0, width, height), Qt.AlignCenter, self.__sectionText)
        painter.setPen(QPen(self.__sectionLineColor, 1, Qt.SolidLine))
        painter.drawLine(0, (height / 2) + 1, 480 - (width / 2 + 5), (height / 2) + 1)
        painter.drawLine(485 + (width / 2), (height / 2) + 1, 940, (height / 2) + 1)


class BaseAccountFormWidget(QWidget):
    _accountType = None
    _formLabelFont = QFont("Nimbus Sans L", 13)
    _descriptionFont = QFont("Nimbus Sans L", 10)
    _formInputFont = QFont("Nimbus Sans L", 11)
    _onInputChanged = pyqtSignal()

    formValidityChanged = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)   
        self.setFixedSize(942, 295)
        layout = self._createCommonAccountFormLayout()
        layout.addLayout(self._createAndSetupDataLayout())
        layout.addStretch(1)
        self.setLayout(layout)

    def _createCommonAccountFormLayout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(80, 0, 0, 0)
        layout.addLayout(self._createIdentifierLayout())
        layout.addLayout(self._createCryptoLayout())
        return layout

    def _createIdentifierLayout(self):
        identifierFormLayout = QHBoxLayout()
        identifierInputFormLayout = QVBoxLayout()

        identifierInputLabel = QLabel("Account identifier")
        identifierInputLabel.setFont(self._formLabelFont)

        self._identifierInput = QLineEdit()
        self._identifierInput.setMaxLength(40)
        self._identifierInput.setFont(self._formInputFont)
        self._identifierInput.textChanged.connect(self._baseInputChanged)

        identifierDescription = QLabel("An arbitrary name to easily identify your cloud account\nin cryptStorePi. This is NOT the username! (max 40 chars.)")
        identifierDescription.setAlignment(Qt.AlignBottom)
        identifierDescription.setFont(self._descriptionFont)

        identifierInputFormLayout.addWidget(identifierInputLabel)
        identifierInputFormLayout.addWidget(self._identifierInput)
        identifierFormLayout.addLayout(identifierInputFormLayout)
        identifierFormLayout.addWidget(identifierDescription)

        return identifierFormLayout

    def _createCryptoLayout(self):
        cryptoFormLayout = QHBoxLayout()
        cryptoInputFormLayout = QVBoxLayout()

        cryptoInputLabel = QLabel("Cryptographic key")
        cryptoInputLabel.setFont(self._formLabelFont)

        self._cryptoInput = QLineEdit()
        self._cryptoInput.setFont(self._formInputFont)
        self._cryptoInput.setMaxLength(16)
        self._cryptoInput.textChanged.connect(self._baseInputChanged)

        cryptoDescription = QLabel("A valid  16 char. long AES-128 key to encode and decode\nthe file shards located on this account.")
        cryptoDescription.setAlignment(Qt.AlignBottom)
        cryptoDescription.setFont(self._descriptionFont)

        cryptoInputFormLayout.addWidget(cryptoInputLabel)
        cryptoInputFormLayout.addWidget(self._cryptoInput)
        cryptoFormLayout.addLayout(cryptoInputFormLayout)
        cryptoFormLayout.addWidget(cryptoDescription)

        return cryptoFormLayout

    def _baseInputChanged(self):
        self.formValidityChanged.emit(self.isFormValid())

    def reset(self):
        self.__resetCommonForm()
        self._resetAccountSpecificDataForm()
        self.formValidityChanged.emit(self.isFormValid())

    def __resetCommonForm(self):
        self._cryptoInput.setText("")
        self._identifierInput.setText("")

    def resetAccountSpecificDataForm(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method '_resetAccountSpecificDataForm'. It should reset all fields to empty and default values.")

    def getAccountData(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'getAccountData'. It should return an instance of models.AccountData.")

    def setAccountData(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'setAccountData'. It should return an instance of models.AccountData.")

    def isFormValid(self):
        cryptoKey = self._cryptoInput.text().strip()
        identifier = self._identifierInput.text().strip()

        return self._validateAccountSpecificForm() and len(identifier) > 0 and len(cryptoKey) == 16

    def _validateAccountSpecificForm(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method '_validateAccountSpecificForm'. It should return a boolean.")

    def _createAndSetupDataLayout(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method '_createAndSetupDataLayout'. It should return a layout representing the specifics of an account.")


class DropboxAccountForm(BaseAccountFormWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self._accountType = AccountTypes.Dropbox
        self._AccountHelpDialog = AccountHelpDialog(scrollWidget=DropboxHelpPage())
        self._AccountHelpDialog.setWindowTitle("How to get a Dropbox API token?")
        self._setupStyle()

    def getAccountData(self):
        accountIdenfitifer = self._identifierInput.text().strip()
        apiToken = self._tokenInput.text().strip()
        cryptoKey = self._cryptoInput.text().strip()
        return AccountData(self._accountType, accountIdenfitifer, cryptoKey, {'apiToken': apiToken})

    def setAccountData(self, accountData):
        self._identifierInput.setText(accountData.identifier)
        self._cryptoInput.setText(accountData.cryptoKey)
        self._tokenInput.setText(accountData.data['apiToken'])

    def _validateAccountSpecificForm(self):
        token = self._tokenInput.text().strip() 
        return len(token) > 0 and re.match("[ -~]", token)

    def _createAndSetupDataLayout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.__createAccountFormLayout())
        layout.addLayout(self.__createHelpButtonLayout())
        layout.addStretch(1)
        return layout

    def _setupStyle(self):
        self.setStyleSheet(
            """
                QLineEdit {border:1px solid #E39910; height:25px; width: 400px; max-width: 400px; margin-right:40px;}
                QLineEdit:focus {border:2px solid #E39910}
                QLineEdit:hover {border:2px solid #E39910}

                QPushButton#helpButton {
                    background-color:#e36410;
                    color:white;
                    max-width:200px;
                    border:0px;
                    height:30px;
                }

                QPushButton#helpButton:pressed {
                    background-color:#e68a4e;
                }
            """
        )

    def _openHelpFrame(self):
        self._AccountHelpDialog.show()

    def _resetAccountSpecificDataForm(self):
        self._tokenInput.setText("")

    def __createAccountFormLayout(self):
        layout = QVBoxLayout()
        tokenFormLayout = QHBoxLayout()
        tokenInputFormLayout = QVBoxLayout()

        tokenInputLabel = QLabel("Dropbox API Access Token")
        tokenInputLabel.setFont(self._formLabelFont)

        self._tokenInput = QLineEdit()
        self._tokenInput.setFont(self._formInputFont)
        self._tokenInput.textChanged.connect(self._baseInputChanged)

        tokenFormDescription = QLabel("For help, click the 'How to get a token?' button!")
        tokenFormDescription.setAlignment(Qt.AlignBottom)
        tokenFormDescription.setFont(self._descriptionFont)

        tokenInputFormLayout.addWidget(tokenInputLabel)
        tokenInputFormLayout.addWidget(self._tokenInput)
        tokenFormLayout.addLayout(tokenInputFormLayout)
        tokenFormLayout.addWidget(tokenFormDescription)

        layout.addLayout(tokenFormLayout)
        layout.addStretch(1)

        return layout

    def __createHelpButtonLayout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(-50, 50, 0, 0)
        helpButton = QPushButton("How to get an access token?")
        helpButton.setObjectName("helpButton")
        helpButton.clicked.connect(self._openHelpFrame)
        layout.addWidget(helpButton, Qt.AlignLeading)

        return layout


class DriveAccountForm(BaseAccountFormWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.__formData = {}
        self._accountType = AccountTypes.GoogleDrive
        self.__INVALID_CREDENTIALS_TEXT = "Invalid service account credentials!"
        self.__accountHelpDialog = AccountHelpDialog(scrollWidget=DriveHelpPage())
        self.__accountHelpDialog.setWindowTitle("How to set up google drive for CryptStorePi")
        self._setupStyle()

    def __createCredentialsDataLabels(self):
        errorLabel = QLabel()
        errorLabel.setFont(self._descriptionFont)
        errorLabel.setObjectName("errorLabel")

        projectIDLabel = QLabel()
        projectIDLabel.setFont(self._descriptionFont)
        projectIDLabel.setObjectName("projectIDLabel")

        clientEmailLabel = QLabel()
        clientEmailLabel.setFont(self._descriptionFont)
        clientEmailLabel.setObjectName("clientEmailLabel")

        clientIDLabel = QLabel()
        clientIDLabel.setFont(self._descriptionFont)
        clientIDLabel.setObjectName("clientIDLabel")

        disclaimerLabel = QLabel("Note: Only a small subset of the credentials data is shown here.")
        disclaimerLabel.setFont(self._descriptionFont)
        disclaimerLabel.setObjectName("disclaimerLabel")
        disclaimerLabel.hide()

        return {
            "errorLabel": errorLabel,
            "projectIDLabel": projectIDLabel,
            "clientEmailLabel": clientEmailLabel,
            "clientIDLabel": clientIDLabel,
            "disclaimerLabel": disclaimerLabel
        }

    def _setupStyle(self):
        self.setStyleSheet(
            """
                QLineEdit {border:1px solid #E39910; height:25px; width: 400px; max-width: 400px; margin-right:40px;}
                QLineEdit:focus {border:2px solid #E39910}
                QLineEdit:hover {border:2px solid #E39910}
                QPushButton#helpButton, QPushButton#openCredentials {
                    background-color:#e36410;
                    color:white;
                    width:180px;
                    border:0px;
                    height:30px;
                }
                QPushButton#helpButton:pressed, QPushButton#openCredentials:pressed {
                    background-color:#e68a4e;
                }
                QWidget#credentialsData{
                    background-color:#ECECEC;
                    border:1px solid #E8E8E8;
                }
                QLabel#disclaimerLabel, QLabel#projectIDLabel, QLabel#clientEmailLabel, QLabel#clientIDLabel{background-color:#ECECEC;}
                QLabel#errorLabel, QLabel#disclaimerLabel{color:red;}
            """
        )

    def _openHelpFrame(self):
        self.__accountHelpDialog.show()

    def _resetAccountSpecificDataForm(self):
        self.__formData = {}
        self.__resetCredentialLabels()

    def getAccountData(self):
        accountIdenfitifer = self._identifierInput.text().strip()
        cryptoKey = self._cryptoInput.text().strip()
        return AccountData(self._accountType, accountIdenfitifer, cryptoKey, {'service_account_credentials': self.__formData['data']})

    def setAccountData(self, accountData):
        self._identifierInput.setText(accountData.identifier)
        self._cryptoInput.setText(accountData.cryptoKey)
        self.__formData = accountData.data['service_account_credentials']

        self.__credentialsLabels['errorLabel'].setText("")
        self.__credentialsLabels['projectIDLabel'].setText(f"Project ID: {self.__formData['project_id']}")
        self.__credentialsLabels['clientEmailLabel'].setText(f"Client Email: {self.__formData['client_email']}")
        self.__credentialsLabels['clientIDLabel'].setText(f"Client ID: {self.__formData['client_id']}")
        self.__credentialsLabels['disclaimerLabel'].show()

    def _validateAccountSpecificForm(self):
        return len(self.__formData.keys())>0

    def _createAndSetupDataLayout(self):
        self.__credentialsLabels = self.__createCredentialsDataLabels()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addLayout(self.__createControlsLayout())
        layout.addWidget(self.__createDriveCredentialsWidget())
        layout.addStretch(1)
        return layout

    def __createControlsLayout(self):
        controlsLayout = QHBoxLayout()
        controlsLayout.setAlignment(Qt.AlignLeading)
        controlsLayout.setContentsMargins(0, 10, 0, 0)
        controlsLayout.setSpacing(5)

        openCredentialsButton = QPushButton("Open Credentials File")
        openCredentialsButton.setObjectName("openCredentials")
        openCredentialsButton.clicked.connect(self.__openCredentialsBrowser)
        controlsLayout.addWidget(openCredentialsButton)

        openHelpButton = QPushButton("How to get credentials?")
        openHelpButton.setObjectName("helpButton")
        openHelpButton.clicked.connect(self._openHelpFrame)
        controlsLayout.addWidget(openHelpButton)

        controlsLayout.addWidget(self.__credentialsLabels['errorLabel'])

        return controlsLayout

    def __openCredentialsBrowser(self):
        credentials_file = QFileDialog.getOpenFileUrl(self, "Select the service account credentials json")[0]
        self.__readCredentialsFile(credentials_file)
        self.formValidityChanged.emit(self.isFormValid())

    def __readCredentialsFile(self, credentials_file):
        credentials_file_path = credentials_file.toLocalFile()
        if credentials_file_path:
            credentials_size = os.stat(credentials_file_path)[6]
            file_extension = credentials_file.fileName().split(".")[-1]
            if credentials_size > 0 and credentials_size < 5000 and file_extension == "json":
                try:
                    with open(credentials_file_path, 'r') as f:
                        credentials = json.loads(f.read())
                        self.__formData['data'] = credentials
                        self.__credentialsLabels['errorLabel'].setText("")
                        self.__credentialsLabels['projectIDLabel'].setText(f"Project ID: {self.__formData['data']['project_id']}")
                        self.__credentialsLabels['clientEmailLabel'].setText(f"Client Email: {self.__formData['data']['client_email']}")
                        self.__credentialsLabels['clientIDLabel'].setText(f"Client ID: {self.__formData['data']['client_id']}")
                        self.__credentialsLabels['disclaimerLabel'].show()
                except json.decoder.JSONDecodeError:
                    self.__credentialsLabels['errorLabel'].setText(self.__INVALID_CREDENTIALS_TEXT)
            else:
                self.__credentialsLabels['errorLabel'].setText(self.__INVALID_CREDENTIALS_TEXT)

    def __createDriveCredentialsWidget(self):
        widget = QWidget()
        widget.setFixedSize(942, 80)
        widget.setAttribute(Qt.WA_StyledBackground)   
        widget.setObjectName("credentialsData")
        widget.setLayout(self.__createDriveCredentialsLayout())

        return widget

    def __createDriveCredentialsLayout(self):
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(5, 5, 5, 5)

        firstRowLayout = QHBoxLayout()
        firstRowLayout.addWidget(self.__credentialsLabels['projectIDLabel'])

        secondRowLayout = QHBoxLayout()
        secondRowLayout.addWidget(self.__credentialsLabels['clientEmailLabel'])
        secondRowLayout.addWidget(self.__credentialsLabels['clientIDLabel'])

        mainLayout.addLayout(firstRowLayout)
        mainLayout.addLayout(secondRowLayout)
        mainLayout.addWidget(self.__credentialsLabels['disclaimerLabel'])
        mainLayout.addStretch(1)

        return mainLayout

    def __createHelpButtonLayout(self):
        pass

    def __resetCredentialLabels(self):
        self.__credentialsLabels['errorLabel'].setText("")
        self.__credentialsLabels['projectIDLabel'].setText("")
        self.__credentialsLabels['clientIDLabel'].setText("")
        self.__credentialsLabels['clientEmailLabel'].setText("")
        self.__credentialsLabels['disclaimerLabel'].hide()


class AccountCard(QWidget):
    onSelected = pyqtSignal(int)
    removeButtonClicked = pyqtSignal(int)

    __unselectedStyle = """
        QWidget#accountCard:hover {border:2px solid #e36410;}
        QWidget#accountCard{border:1px solid #e36410;}

        QPushButton#removeButton{border:1px solid #e36410; max-width:20px; height:38px; margin-left:1px;}
        QPushButton#removeButton:hover{border:2px solid #e36410;}
    """
    __selectedStyle = """
        QWidget#accountCard{border:2px solid #e36410;}

        QPushButton#removeButton{border:1px solid #e36410; max-width:20px; height:38px; margin-left:1px;}
        QPushButton#removeButton:hover{border:2px solid #e36410;}
    """

    def __init__(self, *args, **kwargs):
        self.__accountData = kwargs.pop("accountData")
        self.__index = kwargs.pop("index")
        super().__init__(*args, **kwargs)
        self.__setup()

    def __setup(self):
        self.setFixedSize(300, 45)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(self.__unselectedStyle)

        self.__accountIcon = QLabel()
        self.__accountIcon.setPixmap(self.__getIconPixmap())
        # self.__identifierLabel = QLabel(self.__accountData.identifier)
        self.__identifierLabel = QLabel(str(self.__index))
        self.__identifierLabel.setFont(QFont("Nimbus Sans L", 11, False))

        mainLayout = QHBoxLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        infoLayout = QHBoxLayout()
        infoLayout.setSpacing(5)
        infoLayout.setAlignment(Qt.AlignLeft)
        infoLayout.addWidget(self.__accountIcon)
        infoLayout.addWidget(self.__identifierLabel)

        containerWidget = QWidget()
        containerWidget.mouseReleaseEvent = self.__onSelected
        containerWidget.setFixedSize(270, 40)
        containerWidget.setObjectName("accountCard")
        containerWidget.setAttribute(Qt.WA_StyledBackground)
        containerWidget.setLayout(infoLayout)

        removeButton = QPushButton("X")
        removeButton.setObjectName("removeButton")
        removeButton.clicked.connect(self.__onRemoveButtonClicked)

        mainLayout.addWidget(containerWidget)
        mainLayout.addWidget(removeButton)

        self.setLayout(mainLayout)

    def setSelected(self, selected):
        self.setStyleSheet(self.__selectedStyle) if selected else self.setStyleSheet(self.__unselectedStyle)

    def getAccountData(self):
        return self.__accountData

    def setAccountData(self, accountData):
        self.__accountData = accountData
        self.__identifierLabel.setText(accountData.identifier)
        self.__updateAccountTypeIcon()

    def setIndex(self, index):
        self.__index = index
        self.__identifierLabel.setText(str(index))

    def __getIconPath(self):
        return ":dropbox.png" if self.__accountData.accountType == AccountTypes.Dropbox else ":googledrive.png"

    def __getIconPixmap(self):
        pixmap = QPixmap(self.__getIconPath())
        pixmap = pixmap.scaled(25, 25, Qt.IgnoreAspectRatio)

        return pixmap

    def __updateAccountTypeIcon(self):
        self.__accountIcon.setPixmap(self.__getIconPixmap())

    def __onRemoveButtonClicked(self):
        self.removeButtonClicked.emit(self.__index)

    def __onSelected(self, _):
        self.onSelected.emit(self.__index)


class FirstStartSummaryWidget(FirstStartWizardMiddleWidget):

    def _setup(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("I AM THE SUMMARY"))
        self.setLayout(layout)

    def _getStyle(self):
        return "QLabel{border:1px solid red;}"

    def canProceed(self):
        return False

    def canGoBack(self):
        return True

    def setSummaryData(self, summary):
        print(summary)
