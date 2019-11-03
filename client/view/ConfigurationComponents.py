import os
from enum import IntEnum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDialog,
    QHBoxLayout, QPushButton, QLineEdit, 
    QRadioButton, QFileDialog,QScrollArea
)

from PyQt5.QtCore import QSettings, Qt, pyqtSignal, pyqtSlot, QRect, QSize
from PyQt5.QtGui import QColor, QPainter, QFont, QPen, QPixmap, QFontMetrics, QIcon

from model.models import AccountData, AccountTypes
from control.services import TaskManager
from view.Utils import LoadingWidget


class HelpDialog(QDialog):

    def __init__(self, *args, **kwargs):
        scrollWidget = kwargs.pop('scrollWidget')
        super().__init__(*args, **kwargs)
        self.setObjectName("self")
        self.setStyleSheet(
            """
                QDialog#self{background-color:white;}
                QPushButton#closeHelpButton{
                    background-color:#e36410;
                    color:white;
                    width:150px;
                    border:0px;
                    height:30px;
                    margin-right:5px;
                }
                QPushButton#closeHelpButton:pressed {background-color:#e68a4e;}
                QLabel, QScrollArea{background-color:white;border:0px;}
            """
        )
        self.setFixedSize(480, 720)
        self._setup(scrollWidget)
    
    def _setup(self, scrollWidget):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        scroll = QScrollArea()
        scroll.setWidget(scrollWidget)
        scroll.setWidgetResizable(False)
        scroll.setFixedHeight(680)
        
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
    """
        This is the wizard widget that is being shown if the user hasn't configured the software yet.
        Inherits from QWidget.
        Displays the first start setup widget, the current stage and controls for moving between stages.
    """
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

        setupAccountsWidget = SetupAccountsWidget()
        setupAccountsWidget.formValidityChanged.connect(self.__checkCanProceed)
        widgetMap[WizardProgressWidget.WIZARD_PROGRESS_STATES.ACCOUNTS] = setupAccountsWidget

        summaryWidget = SetupNetworkWidget()
        summaryWidget.formValidityChanged.connect(self.__checkCanProceed)
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
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 10, 10)
        controlLayout.setSpacing(20)
        controlLayout.setAlignment(Qt.AlignTrailing)
        controlLayout.addWidget(self.__previousButton)
        controlLayout.addWidget(self.__nextButton)

        self.__layout.addLayout(controlLayout)
        self.setLayout(self.__layout)

    def __goNext(self):
        self.__widgetMap[self.__state].hide()
        self.__state = self.__progressWidget.toNextState()
        self.__widgetMap[self.__state].show()
        self.__widgetMap[self.__state].initData()
        self.__update()
        

    def __goBack(self):
        self.__widgetMap[self.__state].hide()
        self.__state = self.__progressWidget.toPreviousState()
        self.__widgetMap[self.__state].show()
        self.__update()

    def __update(self):
        self.__nextButton.setDisabled(not self.__widgetMap[self.__state].canProceed())
        self.__previousButton.setDisabled(not self.__widgetMap[self.__state].canGoBack())
        self.__progressWidget.update()
        self.update()


class WizardProgressWidget(QWidget):
    """
        This widget shows the progress of the FirstStartWizard widget.
        Inherits from QWidget.
        It has an inner enum class for state tracking.
        The widget itself is rendered manually via a custom paint method.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__state = WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME
        self.__activeStateColor = QColor('#E39910')
        self.__inactiveStateColor = QColor('#D8D8D8')
        self.__separatorLineColor = QColor('#777777')
        self.__stageIndexFont = QFont('Arial', 32, QFont.Bold, False)
        self.__stageLabelFont = QFont('Arial', 10, QFont.Bold, False)
        self.setFixedSize(1280, 160)

    def paintEvent(self, e):
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
        welcomeLabelFont = QFont('Helvetica', 42, QFont.Normal)
        welcomeLabelFont.setUnderline(True)
        welcomeLabel.setFont(welcomeLabelFont)

        welcomeInstructionsLabel = QLabel("This wizard will guide you through the first setup of this application.")
        welcomeInstructionsLabel.setFont(QFont('Helvetica', 22, QFont.Normal))
        welcomeInstructionsLabel.setAttribute(Qt.WA_TranslucentBackground)
        continueInstructionLabel = QLabel("To start, click 'Next'!")
        continueInstructionLabel.setFont(QFont('Helvetica', 16, QFont.Normal))
        continueInstructionLabel.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(welcomeLabel, 0, Qt.AlignHCenter | Qt.AlignTop)
        layout.addWidget(welcomeInstructionsLabel, 0, Qt.AlignHCenter)
        layout.addWidget(continueInstructionLabel, 0, Qt.AlignHCenter)
        self.setLayout(layout)

    def canProceed(self):
        return True

    def canGoBack(self):
        return True

    def _getStyle(self):
        self.setObjectName("welcomeWidget")
        return "#welcomeWidget{background-image:url(./view/assets/encryptionBackground.png);background-repeat:no-repeat;background-position:center;}"


class SetupNetworkWidget(FirstStartWizardMiddleWidget):

    def canProceed(self):
        return True
        return self.__isConnectionOK and self.__isSshOK and len(self.__chosenDirectoryPath) > 0

    def canGoBack(self):
        return True

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

            QLineEdit#sshUsername{max-width: 290px; margin-right:20px;}
            QLineEdit#sshPassword{max-width: 290px; margin-right:40px;}
        """

    def _setup(self):
        self.__formLabelFont = QFont("Helvetica", 13)
        self.__descriptionFont = QFont("Helvetica", 10)
        self.__formInputFont = QFont("Helvetica", 11)

        self.__isConnectionOK = False
        self.__isSshOK = False

        self.__network_data = {"remote": {"address": None, "port": None}, "ssh":{"username": None, "password": None}}
        self.__chosenDirectoryPath = ""

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

        remoteHostNameLabel = QLabel("Remote host")
        remoteHostNameLabel.setFont(self.__formLabelFont)
        remoteHostDescription = QLabel("Resolveable address of the remote host, eg.: localhost or 10.20.30.40 \nand port, eg.: 12345")
        remoteHostDescription.setFont(self.__descriptionFont)
        remoteHostDescription.setAlignment(Qt.AlignBottom)

        self.__remoteHostNameInput = QLineEdit()
        self.__remoteHostNameInput.setObjectName("hostName")
        self.__remoteHostNameInput.setFont(QFont("Helvetica", 12))
        self.__remoteHostNameInput.textChanged.connect(self.__onFormInputChanged)
        remoteHostNameInputLayout.addWidget(remoteHostNameLabel)
        remoteHostNameInputLayout.addWidget(self.__remoteHostNameInput)

        remoteHostPortLabel = QLabel("Port")
        remoteHostPortLabel.setFont(self.__formLabelFont)
        self.__remotePortInput = QLineEdit()
        self.__remotePortInput.setObjectName("hostPort")
        self.__remotePortInput.setFont(self.__formInputFont)
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
        testRemoteHostButton = QPushButton("Test Connection")
        testRemoteHostButton.setObjectName("testConnection")
        testRemoteHostButton.clicked.connect(self.__test_connection)
        remoteHostTestLayout.addWidget(testRemoteHostButton)
        remoteHostTestLayout.addWidget(self.__remoteHostTestResultLabel)
        remoteHostTestLayout.setContentsMargins(0, 5, 0, 0)
        remoteHostTestLayout.setAlignment(Qt.AlignLeft)

        hostLayout.addLayout(hostFormLayout)
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
        self.__sshPasswordInput = QLineEdit()
        self.__sshPasswordInput.setObjectName("sshPassword")
        self.__sshPasswordInput.setFont(self.__formInputFont)
        self.__sshPasswordInput.textChanged.connect(self.__onFormInputChanged)
        sshFormPasswordInputLayout.addWidget(sshPasswordLabel)
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
        self.__syncDirInput.setFont(QFont("Helvetica", 12))
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

    def __test_connection(self):
        self.__remoteHostTestResultLabel.setStyleSheet("color:green;")
        self.__remoteHostTestResultLabel.setText("OK")
        self.__isConnectionOK = True

        self.formValidityChanged.emit()

    def __test_ssh_connection(self):
        self.__SSHTestResultLabel.setStyleSheet("color:green;")
        self.__SSHTestResultLabel.setText("OK")
        self.__isSshOK = True

        self.formValidityChanged.emit()
    
    def __openDirectoryBrowser(self):
        self.__chosenDirectoryPath = str(QFileDialog.getExistingDirectory(self, "Select the synchronization directory"))
        self.__syncDirInput.setText(self.__chosenDirectoryPath)
        self.formValidityChanged.emit()

    def __onFormInputChanged(self):
        self.__isSshOK = False
        self.__isConnectionOK = False
        self.__SSHTestResultLabel.setText("")
        self.__remoteHostTestResultLabel.setText("")
        self.formValidityChanged.emit()


class SetupAccountsWidget(FirstStartWizardMiddleWidget):
    __inited = False

    def canProceed(self):
        return len(self.__formData) > 0

    def canGoBack(self):
        return True

    def initData(self):
        if not self.__inited:
            self.__formData = []
            taskManager = TaskManager.getInstance()
            taskManager.retrieveAccounts(self.__onAccountsRetrieved)

    def _getStyle(self):
        return ""

    def _setup(self):
        self.__layout = QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)

        self.__loadingWidget = LoadingWidget()
        self.__accountsWidget = AccountsWidget()

        self.__layout.addWidget(self.__loadingWidget)
        self.__layout.addWidget(self.__accountsWidget)
        self.__accountsWidget.hide()
        self.setLayout(self.__layout)

    def __onAccountsRetrieved(self, accounts):
        self.__inited = True
        self.__accountsWidget.setAccountData(accounts)
        self.__loadingWidget.hide()
        self.__accountsWidget.show()


class AccountsWidget(QWidget):

    __hasAccountData = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(1280, 480)
        self.setStyleSheet("QWidget#noAccountsWidget{border-right:2px solid #777777;}")
        self.__setup()
    
    def __setup(self):
        self.__noAccountsWidget = QLabel("No accounts could be found, please create new accounts by clicking the 'Add new account' button on the right hand side. \nYou can have a total of 8 accounts.")
        self.__noAccountsWidget.setFont(QFont("Helvetica", 13, False))
        self.__noAccountsWidget.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.__noAccountsWidget.setObjectName("noAccountsWidget")

        self.__accountEditorWidget = AccountEditorWidget()
        self.__accountEditorWidget.hide()
        self.__accountListWidget = AccountListWidget()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.__noAccountsWidget)
        layout.addWidget(self.__accountEditorWidget)
        layout.addLayout(self.__createAccountListLayout())

        self.setLayout(layout)

    def __createAccountListLayout(self):
        layout = QVBoxLayout()
        self.__accountListWidget.accountSelected.connect(self.__accountEditorWidget.setAccountData)
        self.__accountListWidget.accountSelected.connect(self.__onAccountSelected)
        self.__accountEditorWidget.onSaveAccount.connect(self.__accountListWidget.updateCurrentlySelectedAccount)
        self.__accountEditorWidget.onRemoveAccount.connect(self.__accountListWidget.removeAccount)
        layout.addWidget(self.__accountListWidget)
        layout.addStretch(1)
        return layout

    def __onAccountSelected(self, _):
        if not self.__hasAccountData:
            self.__hasAccountData = True
            self.__noAccountsWidget.hide()
            self.__accountEditorWidget.show()

    def setAccountData(self, accounts):
        self.__accountListWidget.setAccounts(accounts)


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
        dropboxButton.setIcon(QIcon('./view/assets/dropbox.png'))
        dropboxButton.setIconSize(accountIconSize)
        dropboxButton.setStyleSheet(self.__activeButtonStyle)
        dropboxButton.clicked.connect(lambda: self.__onAccountTypeSelected(0))

        driveButton = QPushButton("Google Drive")
        driveButton.setIcon(QIcon('./view/assets/googledrive.png'))
        driveButton.setIconSize(accountIconSize)
        driveButton.setStyleSheet(self.__inactiveButtonStyle)
        driveButton.clicked.connect(lambda: self.__onAccountTypeSelected(1))

        return [dropboxButton, driveButton]

    def __onAccountTypeSelected(self, index):
        if index != self.__selectedAccountTypeIndex:
            self.__updateAccountTypeButtons(index)
            self.__displayNewAccountForm(index)
            self.__selectedAccountTypeIndex = index
            self.__saveAccountButton.setEnabled(self.__accountForms[self.__selectedAccountTypeIndex].isFormValid())

    def __updateAccountTypeButtons(self, index):
        self.__accountTypeButtons[self.__selectedAccountTypeIndex].setStyleSheet(self.__inactiveButtonStyle)
        self.__accountTypeButtons[index].setStyleSheet(self.__activeButtonStyle)
    
    def __displayNewAccountForm(self, index):
        self.__accountForms[self.__selectedAccountTypeIndex].hide()
        self.__selectedAccountTypeIndex = index
        self.__accountForms[index].show()

    def __removeAccountClicked(self):
        self.onRemoveAccount.emit()

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
        self.__sectionFont = QFont(QFont('Helvetica', 12, QFont.Bold))
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


class AccountListWidget(QWidget):
    accountSelected = pyqtSignal(object)
    __selectedAccountIndex = -1
    __accountCards = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(320, 480)
        self.setAttribute(Qt.WA_StyledBackground)   
        self.setStyleSheet(
            """
                QPushButton#newAccountButton{height: 25px; border:1px dashed #e36410;width:300px; max-width:300px;}
                QPushButton#newAccountButton:hover{border:2px dashed #e36410; width:300px; max-width:300px;}
            """
        )
        self.__setup()

    def __setup(self):
        self.__layout = QVBoxLayout()
        self.__layout.setSpacing(2)
        self.__layout.setContentsMargins(2,2,2,0)
        self.__layout.setAlignment(Qt.AlignTop)

        self.__newAccountButton = QPushButton("Add new account")
        self.__newAccountButton.setFont(QFont("Helvetica", 10))
        self.__newAccountButton.setObjectName("newAccountButton")
        self.__newAccountButton.clicked.connect(self.__addBlankAccount)

        self.__layout.addWidget(self.__newAccountButton)
        self.__layout.addStretch(1)
        self.setLayout(self.__layout)

    def __addBlankAccount(self):
        blankAccount = AccountData(AccountTypes.Dropbox, "New Account", "", {"apiToken":""})
        self.__addAccount(blankAccount)
        self.__selectAccount(len(self.__accountCards) - 1)
        if len(self.__accountCards) == 8:
            self.__newAccountButton.hide()

    def __addAccount(self, account):
        index = self.__layout.count() - 2
        accountCard = AccountCard(accountData=account)
        accountCard.mouseReleaseEvent = lambda event:self.__selectAccount(index)

        self.__accountCards.append(accountCard)
        self.__layout.insertWidget(index, accountCard, Qt.AlignHCenter)

    def removeAccount(self):
        self.__accountCards[-1].hide()
        self.__layout.removeWidget(self.__accountCards[-1])
        del self.__accountCards[-1]

    def updateCurrentlySelectedAccount(self, account):
        self.__accountCards[self.__selectedAccountIndex].setAccountData(account)

    def setAccounts(self, accounts):
        if self.__layout.count() > 2:
            self.__removeAllAccounts()

        for account in accounts:
            self.addAccount(account)

    def __removeAllAccounts(self):
        for account, index in zip(self.__accountCards, range(0, len(self.__accountCards))):
            account.hide()
            self.__layout.removeWidget(account)
        self.__accounts = []

    def __selectAccount(self, index):
        if index != self.__selectedAccountIndex:
            if self.__selectedAccountIndex > -1:
                self.__accountCards[self.__selectedAccountIndex].setSelected(False)
            self.__accountCards[index].setSelected(True)
            self.__selectedAccountIndex = index
            self.accountSelected.emit(self.__accountCards[index].getAccountData())


class BaseAccountFormWidget(QWidget):
    _accountType = None
    _formLabelFont = QFont("Helvetica", 13)
    _descriptionFont = QFont("Helvetica", 10)
    _formInputFont = QFont("Helvetica", 11)

    formValidityChanged = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self._identifierInput.textChanged.connect(self._onInputChanged)

        identifierDescription = QLabel("An arbitrary name to easily identify your cloud account\nin cryptStorePi. This is NOT the username!")
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
        self._cryptoInput.textChanged.connect(self._onInputChanged)

        cryptoDescription = QLabel("A valid  16 char. long AES-128 key to encode and decode\nthe file shards located on this account.")
        cryptoDescription.setAlignment(Qt.AlignBottom)
        cryptoDescription.setFont(self._descriptionFont)
        
        cryptoInputFormLayout.addWidget(cryptoInputLabel)
        cryptoInputFormLayout.addWidget(self._cryptoInput)
        cryptoFormLayout.addLayout(cryptoInputFormLayout)
        cryptoFormLayout.addWidget(cryptoDescription)

        return cryptoFormLayout
    
    def reset(self):
        self.__resetCommonForm()
        self._resetAccountSpecificDataForm()

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
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method 'isFormValid'. It should return a boolean.")

    def _createAndSetupDataLayout(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method '_createAndSetupDataLayout'. It should return a layout representing the specifics of an account.")


class APITokenAccountFormWithHelpDialogWidget(BaseAccountFormWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def isFormValid(self):
        return self.__validateTokenInput() and  self. __validateIdentifierInput() and self.__validateCryptoInput()

    def _createAndSetupDataLayout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.__createAccountFormLayout())
        layout.addLayout(self.__createHelpButtonLayout())
        layout.addStretch(1)
        return layout

    def _getTokenInputLabel(self):
        raise NotImplementedError(f"Derived class '{self.__class__}' must implement method '_getTokenDescription'. It should create and return a Dialog widget.")

    def __createAccountFormLayout(self):
        layout = QVBoxLayout()
        tokenFormLayout = QHBoxLayout()
        tokenInputFormLayout = QVBoxLayout()

        tokenInputLabel = QLabel(self._getTokenInputLabel())
        tokenInputLabel.setFont(self._formLabelFont)

        self._tokenInput = QLineEdit()
        self._tokenInput.setFont(self._formInputFont)
        self._tokenInput.textChanged.connect(self._onInputChanged)

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

    def _onInputChanged(self):
        self.formValidityChanged.emit(self.isFormValid())

    def _setupStyle(self):
        self.setStyleSheet(
            """
                QLineEdit {border:1px solid #E39910; height:25px; width: 400px; max-width: 400px; margin-right:40px;}
                QLineEdit:focus {border:2px solid #E39910}
                QLineEdit:hover {border:2px solid #E39910}

                QPushButton#helpButton {
                    background-color:#e36410;
                    color:white;
                    max-width:150px;
                    border:0px;
                    height:30px;
                }

                QPushButton#helpButton:pressed {
                    background-color:#e68a4e;
                }
            """
        )

    def _openHelpFrame(self):
        self._helpDialog.show()

    def _resetAccountSpecificDataForm(self):
        self._tokenInput.setText("")

    def __validateTokenInput(self):
        return len(self._tokenInput.text().strip()) > 0
    
    def __validateIdentifierInput(self):
        return len(self._identifierInput.text().strip()) > 0
    
    def __validateCryptoInput(self):
        return len(self._cryptoInput.text().strip()) == 16


class DropboxAccountForm(APITokenAccountFormWithHelpDialogWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accountType = AccountTypes.Dropbox
        self._helpDialog = HelpDialog(scrollWidget=QLabel("SOME HELP LABEL LOL."))
        self._helpDialog.setWindowTitle("How to get a Dropbox API token?")

    def _getTokenInputLabel(self):
        return "Dropbox API Access Token"


class DriveAccountForm(APITokenAccountFormWithHelpDialogWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accountType = AccountTypes.GoogleDrive

    def _getTokenInputLabel(self):
        return "Google Drive API Access Token"
    
    def _openHelpFrame(self):
        print("Opening drive help dialog!")


class AccountCard(QWidget):
    __unselectedStyle = """
        QWidget#accountCard:hover {border:2px solid #e36410;}
        QWidget#accountCard{border:1px solid #e36410;}
    """
    __selectedStyle = """
        QWidget#accountCard{border:2px solid #e36410;}
    """

    def __init__(self, *args, **kwargs):
        self.__accountData = kwargs.pop('accountData')
        super().__init__(*args, **kwargs)
        self.__setup()

    def __setup(self):
        self.setFixedSize(300, 45)
        self.setStyleSheet(self.__unselectedStyle)
        self.setObjectName("accountCard")
        self.setAttribute(Qt.WA_StyledBackground)   

        self.__accountIcon = QLabel()
        self.__accountIcon.setPixmap(self.__getIconPixmap())
        self.__identifierLabel = QLabel(self.__accountData.identifier)
        self.__identifierLabel.setFont(QFont("Helvetica", 11, False))

        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.__accountIcon)
        layout.addWidget(self.__identifierLabel)

        self.setLayout(layout)

    def setSelected(self, selected):
        self.setStyleSheet(self.__selectedStyle) if selected else self.setStyleSheet(self.__unselectedStyle)

    def getAccountData(self):
        return self.__accountData

    def setAccountData(self, accountData):
        self.__accountData = accountData
        self.__identifierLabel.setText(accountData.identifier)
        self.__updateAccountTypeIcon()

    def __getIconPath(self):
        return "./view/assets/dropbox.png" if self.__accountData.accountType == AccountTypes.Dropbox else "./view/assets/googledrive.png"

    def __getIconPixmap(self):
        pixmap = QPixmap(self.__getIconPath())
        pixmap = pixmap.scaled(25, 25, Qt.IgnoreAspectRatio)
        
        return pixmap
    
    def __updateAccountTypeIcon(self):
        self.__accountIcon.setPixmap(self.__getIconPixmap())