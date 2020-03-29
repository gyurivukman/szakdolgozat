import os
import re
import json

from enum import IntEnum
from uuid import uuid4

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QDialog, QHBoxLayout, QPushButton,
    QLineEdit, QFileDialog, QScrollArea
)

from view.firststart.help import DropboxHelpPage, DriveHelpPage

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRect, QSize
from PyQt5.QtGui import QColor, QPainter, QFont, QPen, QPixmap, QFontMetrics, QIcon

from model.config import AccountData, AccountTypes
from model.message import NetworkMessage, MessageTypes
from view import resources
from view.loaders import LoaderWidget
from view.firststart.abstract import FirstStartWizardMiddleWidget, SetupableComponent


class AccountHelpDialog(QDialog, SetupableComponent):

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


class SetupAccountsWrapperWidget(FirstStartWizardMiddleWidget):
    __inited = False
    __canProceed = True

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

    def canProceed(self):
        return self.__canProceed

    def canGoBack(self):
        return True

    def initData(self):
        self._serviceHub.startNetworkService()
        self._serviceHub.connect()
        raw = {"header": {"messageType": MessageTypes.GET_ACCOUNT_LIST, "uuid": uuid4().hex}, "data": None}
        self._serviceHub.sendNetworkMessage(NetworkMessage(raw), self.__onAccountsRetrieved)

    def getFormData(self):
        return self.__accountsWidget.getAccounts()

    def isInited(self):
        return self.__inited

    def invalidate(self):
        self.__inited = False
        self.__accountsWidget.removeAllAccounts()
        self.__accountsWidget.hide()
        self.__loadingWidget.show()
        if self._serviceHub.isNetworkServiceRunning():
            self._serviceHub.shutdownNetwork()
            self._serviceHub.initNetworkService()

    def __onAccountsRetrieved(self, accounts):
        self._serviceHub.disconnect()
        self.__inited = True
        self.__accountsWidget.setAccounts(accounts)
        self.__loadingWidget.hide()
        self.__accountsWidget.show()

    def __onAccountListChanged(self, event):
        self.formValidityChanged.emit(self.__canProceed)


class SetupAccountsWidget(QWidget, SetupableComponent):

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
        self._setup()

    def _setup(self):
        self.__noAccountsWidget = QLabel("No accounts could be found, please create new accounts by clicking the 'Add new account' button on the right hand side. \nYou can have a total of 8 accounts.")
        self.__noAccountsWidget.setFont(QFont("Nimbus Sans L", 13, False))
        self.__noAccountsWidget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.__noAccountsWidget.setObjectName("noAccountsWidget")

        self.__accountEditorWidget = AccountEditorWidget()
        self.__accountEditorWidget.onSaveAccount.connect(self.__onAccountSaveClicked)
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
        accountCard.onSelected.connect(self.__onAccountCardSelected)  # TODO disconnect
        accountCard.removeButtonClicked.connect(self.__onAccountCardRemoveClicked)  # TODO disconnect

        self.__accountCardWidgets.append(accountCard)
        self.__accountListLayout.insertWidget(index, accountCard, Qt.AlignHCenter)

    def __selectAccount(self, index):
        if self.__selectedAccountIndex is not None:
            self.__accountCardWidgets[self.__selectedAccountIndex].setSelected(False)
        self.__selectedAccountIndex = index
        self.__accountCardWidgets[index].setSelected(True)
        self.__accountEditorWidget.setAccountData(self.__accountCardWidgets[index].getAccountData())

    def __setNoAccountsAvailable(self):
        self.__selectedAccountIndex = None
        self.__accountEditorWidget.hide()
        self.__noAccountsWidget.show()

    def __removeAccountCardAt(self, index):
        self.__accountCardWidgets[index].hide()
        self.__accountListLayout.removeWidget(self.__accountCardWidgets[index])
        del self.__accountCardWidgets[index]

    def getAccounts(self):
        return [accountCard.getAccountData() for accountCard in self.__accountCardWidgets]

    def setAccounts(self, accounts):
        accountCount = len(accounts)
        for accountData in accounts:
            self.__addAccountWidget(accountData)

        if accountCount > 0:
            self.__selectAccount(0)
            self.__noAccountsWidget.hide()
            self.__accountEditorWidget.show()

    def removeAllAccounts(self):
        self.__setNoAccountsAvailable()
        for index in range(len(self.__accountCardWidgets)):
            self.__accountCardWidgets[index].hide()
            self.__accountListLayout.removeWidget(self.__accountCardWidgets[index])

        del self.__accountCardWidgets
        self.__accountCardWidgets = []

    def __onAccountSaveClicked(self, account):
        self.__accountCardWidgets[self.__selectedAccountIndex].setAccountData(account)

    def __onAccountCardSelected(self, index):
        if self.__selectedAccountIndex is not None:
            self.__accountCardWidgets[self.__selectedAccountIndex].setSelected(False)
        self.__selectAccount(index)

    def __onAccountCardRemoveClicked(self, index):
        self.__removeAccountCardAt(index)
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
            self.__setNoAccountsAvailable()

    def __onAddNewAccountClicked(self, _):
        self.__addBlankAccount()
        if not self.__accountEditorWidget.isVisible():
            self.__noAccountsWidget.hide()
            self.__accountEditorWidget.show()


class AccountEditorWidget(QWidget, SetupableComponent):
    onSaveAccount = pyqtSignal(object)

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
        self.setObjectName("accountEditor")
        self.setStyleSheet("#accountEditor{border-right:2px solid #777777;}")
        self.__accountForms = self.__createAccountForms()
        self._setup()

    def __createAccountForms(self):
        return [DropboxAccountForm(), DriveAccountForm()]

    def _setup(self):
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
        self.__saveAccountButton.setStyleSheet(
            """
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
        self.__saveAccountButton.setFocusPolicy(Qt.NoFocus)
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
        return len(self.__formData.keys()) > 0

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


class AccountCard(QWidget, SetupableComponent):
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
        self._setup()

    def _setup(self):
        self.setFixedSize(300, 45)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(self.__unselectedStyle)

        self.__accountIcon = QLabel()
        self.__accountIcon.setPixmap(self.__getIconPixmap())
        self.__identifierLabel = QLabel(self.__accountData.identifier)
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
        removeButton.setFocusPolicy(Qt.NoFocus)

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
