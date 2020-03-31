from os.path import expanduser
from socket import gaierror
from paramiko.ssh_exception import NoValidConnectionsError, AuthenticationException


from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog,
    QCheckBox
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIntValidator, QPixmap

from model.events import ConnectionEventTypes, ConnectionEvent
from model.iconsizes import IconSizes
from model.config import ServerConfig, NetworkConfig, SshConfig
from view import resources
from view.firststart.abstract import FirstStartWizardMiddleWidget


class SetupNetworkWidget(FirstStartWizardMiddleWidget):

    def __init__(self, *args, **kwargs):
        self.__chosenDirectoryPath = None

        self.__testSuccessIcon = self.__createIcon(":check.png")
        self.__testFailedIcon = self.__createIcon(":warning.png")

        self.__hostConnectionTestResultIcon = QLabel()
        self.__SSHConnectionTestResultIcon = QLabel()

        self.__hostTestButton = None
        self.__sshTestButton = None

        super().__init__(*args, **kwargs)

    def __createIcon(self, resourcePath):
        return QPixmap(resourcePath).scaled(24, 24, Qt.IgnoreAspectRatio)

    def canProceed(self):
        return self.__isConnectionOK and self.__isSshOK and self.__chosenDirectoryPath is not None

    def canGoBack(self):
        return True

    def getFormData(self):
        serverConfig = ServerConfig(self.__remoteHostNameInput.text(), self.__remotePortInput.text(), self.__aesKeyInput.text())
        sshConfig = SshConfig(self.__sshUsernameInput.text(), self.__sshPasswordInput.text())

        networkConfig = NetworkConfig(serverConfig, sshConfig, self.__chosenDirectoryPath)

        return networkConfig

    def _getStyle(self):
        return """
            QLineEdit {border:1px solid #E39910; height:25px;}
            QLineEdit:focus {border:2px solid #E39910}
            QLineEdit:hover {border:2px solid #E39910}

            QPushButton {width: 150px; max-width:150px; height:25px; border:0; margin-right:20px; background-color:#e36410; color:white;}
            QPushButton:disabled {background-color:#D8D8D8;}
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
        self.__remoteHostNameInput.textChanged.connect(self.__onHostFormInputChanged)
        remoteHostNameInputLayout.addWidget(remoteHostNameLabel)
        remoteHostNameInputLayout.addWidget(self.__remoteHostNameInput)

        remoteHostPortLabel = QLabel("Port")
        remoteHostPortLabel.setFont(self.__formLabelFont)
        self.__remotePortInput = QLineEdit()
        self.__remotePortInput.setObjectName("hostPort")
        self.__remotePortInput.setFont(self.__formInputFont)
        self.__remotePortInput.setValidator(QIntValidator(0, 65535))
        self.__remotePortInput.textChanged.connect(self.__onHostFormInputChanged)
        remoteHostPortInputLayout.addWidget(remoteHostPortLabel)
        remoteHostPortInputLayout.addWidget(self.__remotePortInput)

        hostFormLayout.addLayout(remoteHostNameInputLayout)
        hostFormLayout.addLayout(remoteHostPortInputLayout)
        hostFormLayout.addWidget(remoteHostDescription)
        hostFormLayout.setContentsMargins(0, 0, 0, 0)
        hostFormLayout.setAlignment(Qt.AlignHCenter)

        self.__remoteHostTestResultLabel = QLabel()
        self.__remoteHostTestResultLabel.setFont(self.__formInputFont)

        aesKeyInputLabel = QLabel("Network encryption key")
        aesKeyInputLabel.setFont(self.__formLabelFont)

        self.__aesKeyInput = QLineEdit()
        self.__aesKeyInput.setObjectName("aesKey")
        self.__aesKeyInput.setFont(self.__formInputFont)
        self.__aesKeyInput.setMaxLength(16)
        self.__aesKeyInput.textChanged.connect(self.__onHostFormInputChanged)

        aesKeyInputLayout.addWidget(aesKeyInputLabel)
        aesKeyInputLayout.addWidget(self.__aesKeyInput)

        aesKeyDescription = QLabel("16 byte AESKey. Example: IAmAProperAesKey")
        aesKeyDescription.setFont(self.__descriptionFont)

        aesKeyFormLayout.addLayout(aesKeyInputLayout)
        aesKeyFormLayout.addWidget(aesKeyDescription)

        self.__hostTestButton = QPushButton("Test Connection")
        self.__hostTestButton.setEnabled(False)
        self.__hostTestButton.setFocusPolicy(Qt.NoFocus)
        self.__hostTestButton.clicked.connect(self.__testConnection)

        remoteHostTestLayout.addWidget(self.__hostTestButton)
        remoteHostTestLayout.addWidget(self.__hostConnectionTestResultIcon)
        remoteHostTestLayout.addSpacing(10)
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
        self.__sshUsernameInput.textChanged.connect(self.__onSshFormInputChanged)
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
        self.__sshPasswordInput.textChanged.connect(self.__onSshFormInputChanged)

        sshFormPasswordInputLayout.addLayout(sshPasswordLabelsLayout)
        sshFormPasswordInputLayout.addWidget(self.__sshPasswordInput)

        self.__SSHTestResultLabel = QLabel()
        self.__SSHTestResultLabel.setFont(self.__formInputFont)

        self.__sshTestButton = QPushButton("Test SSH")
        self.__sshTestButton.setEnabled(False)
        self.__sshTestButton.setFocusPolicy(Qt.NoFocus)
        self.__sshTestButton.clicked.connect(self.__testSSHConnection)
        sshFormTestConnectionLayout.addWidget(self.__sshTestButton)
        sshFormTestConnectionLayout.addWidget(self.__SSHConnectionTestResultIcon)
        sshFormTestConnectionLayout.addSpacing(10)
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

    def __checkboxStateChanged(self, state):
        echoMode = QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password
        self.__sshPasswordInput.setEchoMode(echoMode)

    def __checkIsHostformFilled(self):
        address = self.__remoteHostNameInput.text()
        port = self.__remotePortInput.text()
        aesKey = self.__aesKeyInput.text()

        canTest = len(address) > 0 and len(port) > 0 and len(aesKey) == 16
        self.__hostTestButton.setEnabled(canTest)

    def __checkIsSshFormFilled(self):
        address = self.__remoteHostNameInput.text()
        username = self.__sshUsernameInput.text()
        password = self.__sshPasswordInput.text()

        canTest = len(address) > 0 and len(username) > 0 and len(password) > 0
        self.__sshTestButton.setEnabled(canTest)

    def __testConnection(self):
        self.__hostConnectionTestResultIcon.hide()
        self.__remoteHostTestResultLabel.hide()
        self._serviceHub.networkStatusChannel.connect(self.__onNetworkEvent)
        address = self.__remoteHostNameInput.text()
        port = self.__remotePortInput.text()
        aesKey = self.__aesKeyInput.text()

        try:
            self._serviceHub.setNetworkInformation(address, int(port), aesKey.encode())
            self._serviceHub.connectToServer()
        except (ConnectionError, gaierror):
            self.__hostConnectionFailed("Couldn't connect to the specified remote.")
            self._serviceHub.disconnectServer()

    def __hostConnectionSuccessful(self):
        self.__isConnectionOK = True
        self.__hostConnectionTestResultIcon.setPixmap(self.__testSuccessIcon)
        self.__hostConnectionTestResultIcon.show()
        self._serviceHub.networkStatusChannel.disconnect(self.__onNetworkEvent)
        self.formValidityChanged.emit()

    def __hostConnectionFailed(self, message):
        self.__isConnectionOK = False
        self.__hostConnectionTestResultIcon.setPixmap(self.__testFailedIcon)
        self.__hostConnectionTestResultIcon.show()
        self.__remoteHostTestResultLabel.setText(message)
        self.__remoteHostTestResultLabel.show()
        self._serviceHub.networkStatusChannel.disconnect(self.__onNetworkEvent)

        self.formValidityChanged.emit()

    def __sshConnectionSuccessful(self):
        self.__isSshOK = True
        self.__SSHConnectionTestResultIcon.setPixmap(self.__testSuccessIcon)
        self.__SSHConnectionTestResultIcon.show()
        self.formValidityChanged.emit()

    def __sshConnectionFailed(self, message):
        self.__isConnectionOK = False
        self.__SSHConnectionTestResultIcon.setPixmap(self.__testFailedIcon)
        self.__SSHConnectionTestResultIcon.show()
        self.__SSHTestResultLabel.setText(message)
        self.__SSHTestResultLabel.show()

        self.formValidityChanged.emit()

    def __testSSHConnection(self):
        self.__SSHConnectionTestResultIcon.hide()

        address = self.__remoteHostNameInput.text()
        username = self.__sshUsernameInput.text()
        password = self.__sshPasswordInput.text()

        try:
            self._serviceHub.setSSHInformation(address, username, password)
            self._serviceHub.connectToSSH()
            self.__sshConnectionSuccessful()
        except (gaierror, NoValidConnectionsError, AuthenticationException) as e:
            self.__sshConnectionFailed(str(e))
        finally:
            self._serviceHub.disconnectSSH()

    def __openDirectoryBrowser(self):
        self.__chosenDirectoryPath = str(QFileDialog.getExistingDirectory(self, "Select the synchronization directory", expanduser("~"), QFileDialog.ShowDirsOnly))
        self.__syncDirInput.setText(self.__chosenDirectoryPath)
        self.formValidityChanged.emit()

    def __onNetworkEvent(self, event):
        if event.eventType == ConnectionEventTypes.HANDSHAKE_SUCCESSFUL:
            self.__hostConnectionSuccessful()
            self._serviceHub.disconnectServer()
        elif event.eventType == ConnectionEventTypes.CONNECTION_ERROR:
            self.__hostConnectionFailed(event.data['message'])
            self._serviceHub.disconnectServer()

    def __onHostFormInputChanged(self):
        self.__hostConnectionTestResultIcon.hide()
        self.__remoteHostTestResultLabel.hide()
        self.__isConnectionOK = False
        self.__checkIsHostformFilled()
        self.__checkIsSshFormFilled()
        self.formValidityChanged.emit()

    def __onSshFormInputChanged(self):
        self.__SSHConnectionTestResultIcon.hide()
        self.__SSHTestResultLabel.hide()
        self.__isSshOK = False
        self.__checkIsSshFormFilled()
        self.formValidityChanged.emit()
