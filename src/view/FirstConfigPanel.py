from PyQt4 import QtCore, QtGui
from AccountDialog import AccountDialog

class FirstConfigPanel(QtGui.QWidget):
    firstConfigFinished = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(FirstConfigPanel, self).__init__(*args, **kwargs)
        self.settings = QtCore.QSettings()
        self.accounts = []
        self.__setup()

    def __setup(self):
        self.setFixedSize(400,500)
        self.__setupBaseLayout()
        self.__setupSyncDirPanel()
        self.__setupRemoteDataPanel()
        self.__setupAccountsPanel()
        self.baseLayout.addStretch()
        self.setLayout(self.baseLayout)
        self.setStyleSheet(
            """
                .QLineEdit{
                    height:20px;
                    width:250px;
                    max-width:250px;
                }
                .QPushButton#testConnectionButton{
                    width:250px;
                    height:30px;
                }
                .QLabel#testResultMessage{
                    margin-left:20px;
                }

                .QLabel#accountWarningMessage{
                    border:2px solid red;
                }
            """
        )

    def __setupBaseLayout(self):
        self.baseLayout = QtGui.QVBoxLayout()
        self.baseLayout.setObjectName("baseLayout")
        self.baseLayout.setContentsMargins(3,0,3,15)
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
        addressPanel.addWidget(QtGui.QLabel("Remote host address:"))
        addressPanel.addWidget(self.addressInputField)
        self.baseLayout.addLayout(addressPanel)

        portPanel = QtGui.QHBoxLayout()
        self.portInputField = QtGui.QLineEdit()
        portPanel.addWidget(QtGui.QLabel("Remote host port:"))
        portPanel.addWidget(self.portInputField)
        self.baseLayout.addLayout(portPanel)
        
        testButtonPanel = QtGui.QHBoxLayout()
        testConnectionButton = QtGui.QPushButton("Test connection")
        testConnectionButton.setObjectName("testConnectionButton")
        testConnectionButton.clicked.connect(self.__testConnection)
        testButtonPanel.addWidget(testConnectionButton)
        
        self.testResultMessage = QtGui.QLabel("")
        self.testResultMessage.setObjectName("testResultMessage")
        testButtonPanel.addWidget(self.testResultMessage)
        self.baseLayout.addLayout(testButtonPanel)

    def __setupAccountsPanel(self):
        accountsPanel = QtGui.QVBoxLayout()

        messagePanel = QtGui.QHBoxLayout()
        messageIcon = QtGui.QLabel()
        messageIcon.setAlignment(QtCore.Qt.AlignLeft)
        messageIcon.setPixmap(QtGui.QPixmap("./resources/warning.png"))
        message = QtGui.QLabel("Warning, you can only set your account(s) credentials up once.\n YOU CANNOT CHANGE THEM LATER!")
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
        self.removeAccountButton.clicked.connect(self.__removeAccount)

        controlsPanel.addWidget(addAccountButton)
        controlsPanel.addWidget(self.editAccountButton)
        controlsPanel.addWidget(self.removeAccountButton)
        controlsPanel.addStretch()
        subContainerPanel.addLayout(controlsPanel)
        accountsPanel.addLayout(subContainerPanel)
        self.baseLayout.addLayout(accountsPanel)

    def __openFileDialog(self):
        selectedDir = QtGui.QFileDialog().getExistingDirectory(self, "Choose the synchronization directory",options=QtGui.QFileDialog.DontUseNativeDialog|QtGui.QFileDialog.ShowDirsOnly)
        self.directoryInputField.setText(selectedDir)

    def __testConnection(self):
        self.testResultMessage.setText("OK")
    
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
        self.accountListWidget.addItem("{} / {}".format(self.accounts[-1]["account_type"], unicode(self.accounts[-1]["display_name"]).encode("utf8")))

    def __editAccount(self):
        self.accountDialog = AccountDialog(self)

    def __removeAccount(self):
        del self.accounts[self.selectedAccountIndex]
        self.accountListWidget.takeItem(self.selectedAccountIndex)
        