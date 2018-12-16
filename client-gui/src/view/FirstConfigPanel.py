import socket

from PyQt4 import QtCore, QtGui
import paramiko

from AccountDialog import AccountDialog


class FirstConfigPanel(QtGui.QWidget):
    firstConfigFinished = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super(FirstConfigPanel, self).__init__()
        self.settings = QtCore.QSettings()
        self.__accounts = []
        self.__setup()

    def __setup(self):
        self.__setupBaseLayout()
        self.__setupWarningMessage()
        self.__setupSyncDirPanel()
        self.__setupRemoteDataPanel()
        self.__setupAccountsPanel()
        saveButton = QtGui.QPushButton("Save")
        saveButton.clicked.connect(self.__finishConfig)
        self.__baseLayout.addStretch()
        self.setLayout(self.__baseLayout)
        self.setStyleSheet(
            """
                .QLineEdit{
                    height:20px;
                    width:250px;
                    max-width:250px;
                }

                .QLabel#testResultMessage{
                    margin-left:20px;
                }

                .QLabel#accountWarningMessage{
                    border:2px solid red;
                }
                .QPushButton#finishButton{
                    height:25px;
                }
            """
        )

    def __setupBaseLayout(self):
        self.__baseLayout = QtGui.QVBoxLayout()
        self.__baseLayout.setObjectName("baseLayout")
        self.__baseLayout.setContentsMargins(3, 0, 3, 15)
        self.__baseLayout.setSpacing(15)
    
    def __setupWarningMessage(self):
        messagePanel = QtGui.QHBoxLayout()
        messageIcon = QtGui.QLabel()
        messageIcon.setAlignment(QtCore.Qt.AlignLeft)
        messageIcon.setPixmap(QtGui.QPixmap("./resources/warning.png"))
        message = QtGui.QLabel("Warning, you can only set your settings up once!\nYOU CANNOT CHANGE THEM LATER!")
        message.setObjectName("accountWarningMessage")
        messagePanel.addWidget(messageIcon)
        messagePanel.addWidget(message)

    def __setupSyncDirPanel(self):
        syncDirPanel = QtGui.QVBoxLayout()
        syncDirPanel.setSpacing(5)
        syncDirPanel.addWidget(QtGui.QLabel("Select the synchronization directory:"))
        controlsPanel = QtGui.QHBoxLayout()
        self.__directoryInputField = QtGui.QLineEdit()
        self.__directoryInputField.setObjectName("dirInput")

        fileDialogButton = QtGui.QPushButton("Select")
        fileDialogButton.clicked.connect(self.__openFileDialog)
        fileDialogButton.setObjectName("selectButton")

        controlsPanel.addWidget(fileDialogButton)
        controlsPanel.addWidget(self.__directoryInputField)

        syncDirPanel.addLayout(controlsPanel)
        self.__baseLayout.addLayout(syncDirPanel)

    def __setupRemoteDataPanel(self):
        addressPanel = QtGui.QHBoxLayout()
        self.__addressInputField = QtGui.QLineEdit()
        addressPanel.addWidget(QtGui.QLabel("Remote host address:"))
        addressPanel.addWidget(self.__addressInputField)
        self.__baseLayout.addLayout(addressPanel)

        portPanel = QtGui.QHBoxLayout()

        sshPortPanel = QtGui.QVBoxLayout()
        sshPortPanel.addWidget(QtGui.QLabel("SSH port:"))
        self.__sshPortField = QtGui.QLineEdit()
        sshPortPanel.addWidget(self.__sshPortField)

        commPortPanel = QtGui.QVBoxLayout()
        commPortPanel.addWidget(QtGui.QLabel("Communications port:"))
        self.__commPortField = QtGui.QLineEdit()
        commPortPanel.addWidget(self.__commPortField)

        portPanel.addLayout(sshPortPanel)
        portPanel.addLayout(commPortPanel)

        self.__baseLayout.addLayout(portPanel)

        remoteUsernamePanel = QtGui.QHBoxLayout()
        self.__remoteUsernameField = QtGui.QLineEdit()
        remoteUsernamePanel.addWidget(QtGui.QLabel("SSH username:"))
        remoteUsernamePanel.addWidget(self.__remoteUsernameField)
        self.__baseLayout.addLayout(remoteUsernamePanel)

        remotePasswordPanel = QtGui.QHBoxLayout()
        self.__remotePasswordField = QtGui.QLineEdit()
        self.__remotePasswordField.setEchoMode(QtGui.QLineEdit.Password)
        remotePasswordPanel.addWidget(QtGui.QLabel("SSH password:"))
        remotePasswordPanel.addWidget(self.__remotePasswordField)
        self.__baseLayout.addLayout(remotePasswordPanel)

        testButtonsPanel = QtGui.QHBoxLayout()

        communicationsKeyPanel = QtGui.QHBoxLayout()
        self.__commKeyField = QtGui.QLineEdit()
        self.__commKeyField.setObjectName("commKeyInput")
        communicationsKeyPanel.addWidget(QtGui.QLabel("Comm. Encryption Key:"))
        communicationsKeyPanel.addWidget(self.__commKeyField)
        self.__baseLayout.addLayout(communicationsKeyPanel)

        testSSHConnectionButton = QtGui.QPushButton("Test SSH")
        testSSHConnectionButton.setObjectName("testSSHConnectionButton")
        testSSHConnectionButton.clicked.connect(self.__testSSHConnection)

        testCommunicationPortButton = QtGui.QPushButton("Test Comm. Port")
        testCommunicationPortButton.setObjectName("testCommPortButton")
        testCommunicationPortButton.clicked.connect(self.__testCommPort)

        testButtonsPanel.addWidget(testSSHConnectionButton)
        testButtonsPanel.addWidget(testCommunicationPortButton)
        self.__baseLayout.addLayout(testButtonsPanel)

    def __setupAccountsPanel(self):
        accountsPanel = QtGui.QVBoxLayout()

        subContainerPanel = QtGui.QHBoxLayout()
        self.__accountListWidget = QtGui.QListWidget()
        self.__accountListWidget.currentRowChanged.connect(self.__selectAccount)
        subContainerPanel.addWidget(self.__accountListWidget)

        controlsPanel = QtGui.QVBoxLayout()
        controlsPanel.setSpacing(5)
        addAccountButton = QtGui.QPushButton("Add Account")
        addAccountButton.clicked.connect(self.__addAccount)

        self.__editAccountButton = QtGui.QPushButton("Edit Account")
        self.__editAccountButton.setEnabled(False)
        self.__editAccountButton.clicked.connect(self.__editAccount)

        self.__removeAccountButton = QtGui.QPushButton("Remove Account")
        self.__removeAccountButton.setEnabled(False)
        self.__removeAccountButton.clicked.connect(self.removeCurrentlySelectedAccountFromGui)

        controlsPanel.addWidget(addAccountButton)
        controlsPanel.addWidget(self.__editAccountButton)
        controlsPanel.addWidget(self.__removeAccountButton)
        controlsPanel.addStretch()
        subContainerPanel.addLayout(controlsPanel)
        accountsPanel.addLayout(subContainerPanel)
        self.__baseLayout.addLayout(accountsPanel)

        finishButton = QtGui.QPushButton("Finish")
        finishButton.setObjectName("finishButton")
        finishButton.clicked.connect(self.__finishConfig)
        self.__baseLayout.addWidget(finishButton)

    def __openFileDialog(self):
        selectedDir = QtGui.QFileDialog().getExistingDirectory(self, "Choose the synchronization directory",options=QtGui.QFileDialog.DontUseNativeDialog|QtGui.QFileDialog.ShowDirsOnly)
        self.__directoryInputField.setText(selectedDir)

    def __testSSHConnection(self):
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy)
            client.connect(str(self.__addressInputField.text()), port=22, username=str(self.__remoteUsernameField.text()), password=str(self.__remotePasswordField.text()))
            self.__showTestResultDialog("SSH Connection successful!")
        except Exception as e:
            self.__showTestResultDialog("SSH Connection failed! reason:\n{}".format(e))
        finally:
            client.close()

    def __testCommPort(self):
        try:
            commConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remoteAddress = (unicode(self.__addressInputField.text()).encode("utf8"), self.__commPortField.text().toInt()[0])
            commConnection.settimeout(4)
            commConnection.connect(remoteAddress)
            self.__showTestResultDialog("Communications port works!")
            commConnection.close()
        except Exception as e:
            self.__showTestResultDialog("Communnications port test failed:\n {}".format(e))

    def __showTestResultDialog(self, msg):
        dialog = QtGui.QMessageBox(self)
        dialog.setWindowTitle("Connection Test Result")
        dialog.setText(msg)
        dialog.exec_()

    def __selectAccount(self, index):
        if not self.__editAccountButton.isEnabled():
            self.__editAccountButton.setEnabled(True)
            self.__removeAccountButton.setEnabled(True)
        self.__selectedAccountIndex = index 

    def __addAccount(self):
        self.__accountDialog = AccountDialog(self)
        self.__accountDialog.dataEmitter.connect(self.__onSaveAccount)
        self.__accountDialog.show()

    def __onSaveAccount(self, accData):
        self.__accountDialog.hide()
        self.__accounts.append(accData)
        self.__accountListWidget.addItem("{} / {}".format(self.__accounts[-1]["account_type"], self.__accounts[-1]["display_name"]))

    def __editAccount(self):
        self.__accountDialog = AccountDialog(self, edit=True, data=self.__accounts[self.__selectedAccountIndex])
        self.__accountDialog.dataEmitter.connect(self.__onEditAccount)
        self.__accountDialog.show()

    def removeCurrentlySelectedAccountFromGui(self):
        del self.__accounts[self.__selectedAccountIndex]
        self.__accountListWidget.takeItem(self.__selectedAccountIndex)
        if(len(self.__accounts) > 0):
            self.__selectedAccountIndex = self.__selectedAccountIndex - 1
            self.__accountListWidget.setCurrentRow(self.__selectedAccountIndex)

    def __onEditAccount(self, accData):
        self.__accountDialog.hide()
        self.__accounts.insert(self.__selectedAccountIndex, accData)
        del self.__accounts[self.__selectedAccountIndex+1]

        displayName = "{} / {}".format(self.__accounts[self.__selectedAccountIndex]["account_type"], self.__accounts[self.__selectedAccountIndex]["display_name"])
        self.__accountListWidget.insertItem(self.__selectedAccountIndex, displayName)    
        self.__accountListWidget.takeItem(self.__selectedAccountIndex+1)

    def __finishConfig(self):
        configs = {}
        configs["syncDir"] = unicode(self.__directoryInputField.text()).encode("utf8")
        configs["remoteAddress"] = unicode(self.__addressInputField.text()).encode("utf8")
        configs["SSH_Port"] = unicode(self.__sshPortField.text()).encode("utf8")
        configs["SSH_username"] = unicode(self.__remoteUsernameField.text()).encode("utf8")
        configs["SSH_password"] = unicode(self.__remotePasswordField.text()).encode("utf8")
        configs["commPort"] = unicode(self.__commPortField.text()).encode("utf8")
        configs["commKey"] = unicode(self.__commKeyField.text()).encode("utf8")
        self.__setConfigs(configs)
        self.firstConfigFinished.emit(self.__accounts)

    def __setConfigs(self, configs):
        for key, value in configs.iteritems():
            self.settings.setValue(key, value)
        self.settings.setValue('is_first_start', False)
        self.settings.sync()
