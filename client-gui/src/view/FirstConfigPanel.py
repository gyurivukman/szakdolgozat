import socket

from PyQt4 import QtCore, QtGui
import paramiko

from AccountDialog import AccountDialog


class FirstConfigPanel(QtGui.QWidget):
    firstConfigFinished = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(FirstConfigPanel, self).__init__()
        self.settings = QtCore.QSettings()
        self.accounts = []
        self.__setup()

    def __setup(self):
        self.__setupBaseLayout()
        self.__setupSyncDirPanel()
        self.__setupRemoteDataPanel()
        self.__setupAccountsPanel()
        saveButton = QtGui.QPushButton("Save")
        saveButton.clicked.connect(self.__finishConfig)
        self.baseLayout.addStretch()
        self.setLayout(self.baseLayout)
        self.setStyleSheet(
            """
                .QLineEdit{
                    height:20px;
                    width:250px;
                    max-width:250px;
                }
                .QPushButton#testConnectionButton, .QPushButton#testCommPortButton{
                    height:25px;
                    width:100px;
                }
                .QLabel#testResultMessage{
                    margin-left:20px;
                }

                .QLabel#accountWarningMessage{
                    border:2px solid red;
                }
                .QPushButton#finishButton{
                    width:100px;
                    max-width:100px;
                    height:35px;
                }
            """
        )

    def __setupBaseLayout(self):
        self.baseLayout = QtGui.QVBoxLayout()
        self.baseLayout.setObjectName("baseLayout")
        self.baseLayout.setContentsMargins(3, 0, 3, 15)
        self.baseLayout.setSpacing(15)

    def __setupSyncDirPanel(self):
        syncDirPanel = QtGui.QVBoxLayout()
        syncDirPanel.setSpacing(5)
        syncDirPanel.addWidget(QtGui.QLabel("Select the synchronization directory:"))
        controlsPanel = QtGui.QHBoxLayout()
        self.directoryInputField = QtGui.QLineEdit()
        self.directoryInputField.setObjectName("dirInput")

        fileDialogButton = QtGui.QPushButton("Select")
        fileDialogButton.clicked.connect(self.__openFileDialog)
        fileDialogButton.setObjectName("selectButton")

        controlsPanel.addWidget(fileDialogButton)
        controlsPanel.addWidget(self.directoryInputField)

        syncDirPanel.addLayout(controlsPanel)
        self.baseLayout.addLayout(syncDirPanel)

    def __setupRemoteDataPanel(self):
        addressPanel = QtGui.QHBoxLayout()
        self.addressInputField = QtGui.QLineEdit()
        addressPanel.addWidget(QtGui.QLabel("SSH host address:"))
        addressPanel.addWidget(self.addressInputField)
        self.baseLayout.addLayout(addressPanel)

        portPanel = QtGui.QHBoxLayout()

        sshPortPanel = QtGui.QVBoxLayout()
        sshPortPanel.addWidget(QtGui.QLabel("SSH port:"))
        self.sshPortInputField = QtGui.QLineEdit()
        sshPortPanel.addWidget(self.sshPortInputField)

        commPortPanel = QtGui.QVBoxLayout()
        commPortPanel.addWidget(QtGui.QLabel("Communications port:"))
        self.commPortInputField = QtGui.QLineEdit()
        commPortPanel.addWidget(self.commPortInputField)

        portPanel.addLayout(sshPortPanel)
        portPanel.addLayout(commPortPanel)

        self.baseLayout.addLayout(portPanel)

        remoteUsernamePanel = QtGui.QHBoxLayout()
        self.remoteUsernameField = QtGui.QLineEdit()
        remoteUsernamePanel.addWidget(QtGui.QLabel("SSH username:"))
        remoteUsernamePanel.addWidget(self.remoteUsernameField)
        self.baseLayout.addLayout(remoteUsernamePanel)

        remotePasswordPanel = QtGui.QHBoxLayout()
        self.remotePasswordField = QtGui.QLineEdit()
        self.remotePasswordField.setEchoMode(QtGui.QLineEdit.Password)
        remotePasswordPanel.addWidget(QtGui.QLabel("SSH password:"))
        remotePasswordPanel.addWidget(self.remotePasswordField)
        self.baseLayout.addLayout(remotePasswordPanel)

        testButtonsPanel = QtGui.QHBoxLayout()

        testSSHConnectionButton = QtGui.QPushButton("Test SSH")
        testSSHConnectionButton.setObjectName("testSSHConnectionButton")
        testSSHConnectionButton.clicked.connect(self.__testSSHConnection)

        testCommunicationPortButton = QtGui.QPushButton("Test Comm. Port")
        testCommunicationPortButton.setObjectName("testCommPortButton")
        testCommunicationPortButton.clicked.connect(self.__testCommPort)

        testButtonsPanel.addWidget(testSSHConnectionButton)
        testButtonsPanel.addWidget(testCommunicationPortButton)
        self.baseLayout.addLayout(testButtonsPanel)

    def __setupAccountsPanel(self):
        accountsPanel = QtGui.QVBoxLayout()

        messagePanel = QtGui.QHBoxLayout()
        messageIcon = QtGui.QLabel()
        messageIcon.setAlignment(QtCore.Qt.AlignLeft)
        messageIcon.setPixmap(QtGui.QPixmap("./resources/warning.png"))
        message = QtGui.QLabel("Warning, you can only set your accounts up once!\nYOU CANNOT CHANGE THEM LATER!")
        message.setObjectName("accountWarningMessage")
        messagePanel.addWidget(messageIcon)
        messagePanel.addWidget(message)

        accountsPanel.addLayout(messagePanel)

        subContainerPanel = QtGui.QHBoxLayout()
        self.accountListWidget = QtGui.QListWidget()
        self.accountListWidget.currentRowChanged.connect(self.__selectAccount)
        subContainerPanel.addWidget(self.accountListWidget)

        controlsPanel = QtGui.QVBoxLayout()
        controlsPanel.setSpacing(5)
        addAccountButton = QtGui.QPushButton("Add Account")
        addAccountButton.clicked.connect(self.__addAccount)

        self.editAccountButton = QtGui.QPushButton("Edit Account")
        self.editAccountButton.setEnabled(False)
        self.editAccountButton.clicked.connect(self.__editAccount)

        self.removeAccountButton = QtGui.QPushButton("Remove Account")
        self.removeAccountButton.setEnabled(False)
        self.removeAccountButton.clicked.connect(self.removeCurrentlySelectedAccountFromGui)

        controlsPanel.addWidget(addAccountButton)
        controlsPanel.addWidget(self.editAccountButton)
        controlsPanel.addWidget(self.removeAccountButton)
        controlsPanel.addStretch()
        subContainerPanel.addLayout(controlsPanel)
        accountsPanel.addLayout(subContainerPanel)
        self.baseLayout.addLayout(accountsPanel)

        finishButton = QtGui.QPushButton("Finish")
        finishButton.setObjectName("finishButton")
        finishButton.clicked.connect(self.__finishConfig)
        self.baseLayout.addWidget(finishButton)

    def __openFileDialog(self):
        selectedDir = QtGui.QFileDialog().getExistingDirectory(self, "Choose the synchronization directory",options=QtGui.QFileDialog.DontUseNativeDialog|QtGui.QFileDialog.ShowDirsOnly)
        self.directoryInputField.setText(selectedDir)

    def __testSSHConnection(self):
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy)
            client.connect(str(self.addressInputField.text()), port=22, username=str(self.remoteUsernameField.text()), password=str(self.remotePasswordField.text()))
            self.__showTestResultDialog("SSH Connection successful!")
        except Exception as e:
            self.__showTestResultDialog("SSH Connection failed! reason:\n{}".format(e))
        finally:
            client.close()

    def __testCommPort(self):
        try:
            commConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remoteAddress = (unicode(self.addressInputField.text()).encode("utf8"), self.commPortInputField.text().toInt()[0])
            commConnection.settimeout(4)
            commConnection.connect(remoteAddress)
            self.__showTestResultDialog("Communications port works!")
        except Exception as e:
            self.__showTestResultDialog("Communnications port test failed:\n {}".format(e))

    def __showTestResultDialog(self, msg):
        dialog = QtGui.QMessageBox(self)
        dialog.setWindowTitle("Connection Test Result")
        dialog.setText(msg)
        dialog.exec_()

    def __selectAccount(self, index):
        if not self.editAccountButton.isEnabled():
            self.editAccountButton.setEnabled(True)
            self.removeAccountButton.setEnabled(True)
        self.selectedAccountIndex = index 

    def __addAccount(self):
        self.accountDialog = AccountDialog(self)
        self.accountDialog.dataEmitter.connect(self.__onSaveAccount)
        self.accountDialog.show()

    def __onSaveAccount(self, accData):
        self.accountDialog.hide()
        self.accounts.append(accData)
        self.accountListWidget.addItem("{} / {}".format(self.accounts[-1]["account_type"], self.accounts[-1]["display_name"]))

    def __editAccount(self):
        self.accountDialog = AccountDialog(self, edit=True, data=self.accounts[self.selectedAccountIndex])
        self.accountDialog.dataEmitter.connect(self.__onEditAccount)
        self.accountDialog.show()

    def removeCurrentlySelectedAccountFromGui(self):
        del self.accounts[self.selectedAccountIndex]
        self.accountListWidget.takeItem(self.selectedAccountIndex)
        if(len(self.accounts) > 0):
            self.selectedAccountIndex = self.selectedAccountIndex - 1
            self.accountListWidget.setCurrentRow(self.selectedAccountIndex)

    def __onEditAccount(self, accData):
        self.accountDialog.hide()
        self.accounts.insert(self.selectedAccountIndex, accData)
        del self.accounts[self.selectedAccountIndex+1]

        displayName = "{} / {}".format(self.accounts[self.selectedAccountIndex]["account_type"], self.accounts[self.selectedAccountIndex]["display_name"])
        self.accountListWidget.insertItem(self.selectedAccountIndex, displayName)    
        self.accountListWidget.takeItem(self.selectedAccountIndex+1)

    def __finishConfig(self):
        configs = {}
        configs["syncDir"] = unicode(self.directoryInputField.text()).encode("utf8")
        configs["SSH_Address"] = unicode(self.addressInputField.text()).encode("utf8")
        configs["SSH_Port"] = unicode(self.sshPortInputField.text()).encode("utf8")
        configs["SSH_username"] = unicode(self.remoteUsernameField.text()).encode("utf8")
        configs["SSH_password"] = unicode(self.remotePasswordField.text()).encode("utf8")
        configs["commPort"] = unicode(self.commPortInputField.text()).encode("utf8")
        self.__setConfigs(configs)
        self.firstConfigFinished.emit()

    def __setConfigs(self, configs):
        for key, value in configs.iteritems():
            self.settings.setValue(key, value)
        self.settings.setValue('is_first_start', False)
        self.settings.sync()
