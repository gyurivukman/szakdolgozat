from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton
)

from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon

from model.config import AccountData, AccountTypes
from model.wizard import WIZARD_PROGRESS_STATES

from view import resources
from view.firststart.abstract import FirstStartWizardMiddleWidget
from view.firststart.abstract import SetupableComponent


class FirstStartSummaryWidget(FirstStartWizardMiddleWidget):
    editPreviousPage = pyqtSignal(WIZARD_PROGRESS_STATES)

    def __init__(self, *args, **kwargs):
        self.__networkSummaryContentPanel = NetworkSummaryContentPanel()
        self.__sshSummaryContentPanel = SshSummaryContentPanel()
        self.__syncDirContentPanel = SyncDirSummaryContentPanel()
        self.__accountsContentPanel = AccountsSummaryContentPanel()
        super().__init__(*args, **kwargs)

    def _setup(self):
        layout = QHBoxLayout()

        networkLayout = QVBoxLayout()

        networkSummaryPanel = FirstStartSummaryPanel(headerText="Network configuration", contentPanel=self.__networkSummaryContentPanel, targetState=WIZARD_PROGRESS_STATES.NETWORK)
        networkSummaryPanel.editButtonClicked.connect(self.__onEditButtonClicked)
        networkLayout.addWidget(networkSummaryPanel)

        sshSummaryPanel = FirstStartSummaryPanel(headerText="SSH configuration", contentPanel=self.__sshSummaryContentPanel, targetState=WIZARD_PROGRESS_STATES.NETWORK)
        sshSummaryPanel.editButtonClicked.connect(self.__onEditButtonClicked)
        networkLayout.addWidget(sshSummaryPanel)

        syncDirPanel = FirstStartSummaryPanel(headerText="Synchronization directory", contentPanel=self.__syncDirContentPanel, targetState=WIZARD_PROGRESS_STATES.NETWORK)
        syncDirPanel.editButtonClicked.connect(self.__onEditButtonClicked)
        networkLayout.addWidget(syncDirPanel)

        accountsSummaryPanel = FirstStartSummaryPanel(headerText="Accounts", contentPanel=self.__accountsContentPanel, targetState=WIZARD_PROGRESS_STATES.ACCOUNTS)
        accountsSummaryPanel.editButtonClicked.connect(self.__onEditButtonClicked)

        layout.addLayout(networkLayout)
        layout.addStretch(1)
        layout.addWidget(accountsSummaryPanel)
        self.setLayout(layout)

    def _getStyle(self):
        return ""

    def canProceed(self):
        return False

    def canGoBack(self):
        return True

    def setSummaryData(self, summary):
        self.__configData = summary
        self.__networkSummaryContentPanel.setData(summary.network.remote)
        self.__sshSummaryContentPanel.setData(summary.network.ssh)
        self.__syncDirContentPanel.setData(summary.network.syncDir)
        self.__accountsContentPanel.setData(summary.accounts)

    def __onEditButtonClicked(self, targetState):
        self.editPreviousPage.emit(targetState)

    def getConfigData(self):
        return self.__configData


class FirstStartSummaryPanel(QWidget, SetupableComponent):
    editButtonClicked = pyqtSignal(WIZARD_PROGRESS_STATES)

    def __init__(self, *args, **kwargs):
        headerText = kwargs.pop("headerText")
        contentPanel = kwargs.pop("contentPanel")
        self._editButtonTargetState = kwargs.pop("targetState")

        super().__init__(*args, **kwargs)

        self.setAttribute(Qt.WA_StyledBackground)
        self._editButton = None
        self.setStyleSheet(self._getStyleSheet())
        self.setLayout(self.__createLayout(headerText, contentPanel))

    def _getStyleSheet(self):
        return """
            QPushButton#summaryEditButton {
                background-color:#e36410;
                color: white;
                border:0px;
                max-height:22;
                width:60px;
            }

            QPushButton#summaryEditButton:pressed {
                background-color: #e68a4e;
            }

            QWidget#contentPanel{
                border:2px solid #e68a4e;
                border-radius:5px;
            }
        """

    def __createLayout(self, headerText, contentPanel):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.setContentsMargins(15, 15, 0, 15)

        panelHeaderLayout = QHBoxLayout()

        headerLabel = QLabel(headerText)
        headerLabel.setFont(QFont("Nimbus Sans L", 16, QFont.Bold, False))

        headerLabelLayout = QHBoxLayout()
        headerLabelLayout.setAlignment(Qt.AlignLeft)
        headerLabelLayout.addWidget(headerLabel)

        self._editButton = QPushButton("Edit")
        self._editButton.setObjectName("summaryEditButton")
        self._editButton.setFocusPolicy(Qt.NoFocus)
        self._editButton.clicked.connect(self._onEditButtonClicked)

        editButtonLayout = QHBoxLayout()
        editButtonLayout.setAlignment(Qt.AlignRight)
        editButtonLayout.addWidget(self._editButton)

        panelHeaderLayout.addLayout(headerLabelLayout)
        panelHeaderLayout.addLayout(editButtonLayout)

        contentPanel.setObjectName("contentPanel")

        layout.addLayout(panelHeaderLayout)
        layout.addWidget(contentPanel)

        return layout

    def _onEditButtonClicked(self):
        self.editButtonClicked.emit(self._editButtonTargetState)


class SummaryContentPanel(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self._dataLabelFont = QFont("Nimbus Sans L", 12, QFont.Bold, False)
        self._dataTextFont = QFont("Nimbus Sans L", 12)
        self.setStyleSheet(self._getStyleSheet())

    def _getStyleSheet(self):
        pass

    def setData(self, data):
        pass


class NetworkSummaryContentPanel(SummaryContentPanel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(720)
        self._setup()

    def _getStyleSheet(self):
        return """
            QLabel{max-height:20px;}
        """

    def _setup(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        layout.setSpacing(10)

        labelsLayout = QVBoxLayout()
        labelsLayout.setAlignment(Qt.AlignTop)
        labelsLayout.setSpacing(5)

        dataTextLayout = QVBoxLayout()
        dataTextLayout.setAlignment(Qt.AlignTop)
        dataTextLayout.setSpacing(5)

        hostAddressLabel = QLabel("Remote host:")
        hostAddressLabel.setFont(self._dataLabelFont)
        self.__hostAddressDataText = QLabel("")
        self.__hostAddressDataText.setFont(self._dataTextFont)

        hostPortLabel = QLabel("Remote port:")
        hostPortLabel.setFont(self._dataLabelFont)
        self.__hostPortDataText = QLabel("")
        self.__hostPortDataText.setFont(self._dataTextFont)

        hostKeyLabel = QLabel("Network key:")
        hostKeyLabel.setFont(self._dataLabelFont)
        self.__hostKeyDataText = QLabel("")
        self.__hostKeyDataText.setFont(self._dataTextFont)

        labelsLayout.addWidget(hostAddressLabel)
        labelsLayout.addWidget(hostPortLabel)
        labelsLayout.addWidget(hostKeyLabel)

        dataTextLayout.addWidget(self.__hostAddressDataText)
        dataTextLayout.addWidget(self.__hostPortDataText)
        dataTextLayout.addWidget(self.__hostKeyDataText)

        layout.addLayout(labelsLayout)
        layout.addLayout(dataTextLayout)

        self.setLayout(layout)

    def setData(self, data):
        self.__hostAddressDataText.setText(data.address)
        self.__hostPortDataText.setText(data.port)
        self.__hostKeyDataText.setText(data.encryptionKey)


class SshSummaryContentPanel(SummaryContentPanel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(720)
        self._setup()

    def _setup(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        layout.setSpacing(10)

        labelsLayout = QVBoxLayout()
        labelsLayout.setAlignment(Qt.AlignTop)
        labelsLayout.setSpacing(5)

        dataTextLayout = QVBoxLayout()
        dataTextLayout.setAlignment(Qt.AlignTop)
        dataTextLayout.setSpacing(5)

        sshUsernameLabel = QLabel("Username:")
        sshUsernameLabel.setFont(self._dataLabelFont)
        self.__sshUsernameDataText = QLabel("")
        self.__sshUsernameDataText.setFont(self._dataTextFont)

        sshPasswordLabel = QLabel("Password:")
        sshPasswordLabel.setFont(self._dataLabelFont)
        self.__sshPasswordDataText = QLabel("")
        self.__sshPasswordDataText.setFont(self._dataTextFont)

        labelsLayout.addWidget(sshUsernameLabel)
        labelsLayout.addWidget(sshPasswordLabel)

        dataTextLayout.addWidget(self.__sshUsernameDataText)
        dataTextLayout.addWidget(self.__sshPasswordDataText)

        layout.addLayout(labelsLayout)
        layout.addLayout(dataTextLayout)

        self.setLayout(layout)

    def setData(self, data):
        self.__sshUsernameDataText.setText(data.username)
        self.__sshPasswordDataText.setText("*" * len(data.password))


class SyncDirSummaryContentPanel(SummaryContentPanel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(720)
        self._setup()

    def _setup(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        layout.setSpacing(10)

        syncDirLabel = QLabel("Path:")
        syncDirLabel.setFont(self._dataLabelFont)
        layout.addWidget(syncDirLabel)

        self.__syncDirDataText = QLabel("")
        self.__syncDirDataText.setFont(self._dataTextFont)
        layout.addWidget(self.__syncDirDataText)

        self.setLayout(layout)

    def setData(self, data):
        self.__syncDirDataText.setText(data)


class AccountsSummaryContentPanel(SummaryContentPanel, SetupableComponent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(400)
        self.setFixedHeight(355)
        self.__identifierFont = QFont("Nimbus Sans L", 14)
        self.__driveIcon = QPixmap(":/googledrive.png").scaled(24, 24, Qt.IgnoreAspectRatio)
        self.__dropboxIcon = QPixmap(":/dropbox.png").scaled(24, 24, Qt.IgnoreAspectRatio)
        self.__accountWidgets = []
        self.__layout = None

        self._setup()

    def _setup(self):
        self.__layout = QVBoxLayout()
        self.__layout.setContentsMargins(5, 5, 5, 5)
        self.__layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.__layout.setSpacing(5)
        self.__layout.addStretch(1)
        self.setLayout(self.__layout)

    def setData(self, accounts):
        currentAccountCount = len(self.__accountWidgets)
        newAccountCount = len(accounts)

        for i in range(newAccountCount):
            identifier = accounts[i].identifier
            pixMap = self.__driveIcon if accounts[i].accountType == AccountTypes.GoogleDrive else self.__dropboxIcon

            if i > currentAccountCount - 1:
                accountWidget = AccountSummaryCard(accountIdentifier=identifier, accountIdentifierFont=self.__identifierFont, accountIcon=pixMap)   
                self.__accountWidgets.append(accountWidget)
                self.__layout.insertWidget(i, accountWidget)
            else:
                self.__accountWidgets[i].setData(identifier, pixMap)
            self.__accountWidgets[i].setUnderline(True) if i < newAccountCount - 1 else self.__accountWidgets[i].setUnderline(False)

        if currentAccountCount > newAccountCount:
            for i in range(newAccountCount, currentAccountCount):
                self.__accountWidgets[i].hide()
                self.__layout.removeWidget(self.__accountWidgets[i])
            del self.__accountWidgets[newAccountCount:]


class AccountSummaryCard(QWidget):

    def __init__(self, *args, **kwargs):
        accountIdentifier = kwargs.pop("accountIdentifier")
        accountIconPixmap = kwargs.pop("accountIcon")
        accountIdentifierFont = kwargs.pop("accountIdentifierFont")

        super().__init__(*args, **kwargs)

        self.__accountIdentifierWidget = QLabel(accountIdentifier)
        self.__accountIdentifierWidget.setFont(accountIdentifierFont)

        self.__accountIconWidget = QLabel()
        self.__accountIconWidget.setPixmap(accountIconPixmap)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__createContainerWidget())
        self.setLayout(layout)

    def __createContainerWidget(self):
        containerWidget = QWidget()
        containerWidget.setContentsMargins(0, 0, 0, 0)
        containerWidget.setObjectName("accountSummaryCardContainer")
        layout = self.__createContainerLayout()

        containerWidget.setLayout(layout)

        return containerWidget

    def __createContainerLayout(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        layout.setSpacing(5)

        layout.addWidget(self.__accountIconWidget)
        layout.addWidget(self.__accountIdentifierWidget)
        layout.addStretch(1)

        return layout

    def setData(self, identifier, iconPixmap):
        self.__accountIdentifierWidget.setText(identifier)
        self.__accountIconWidget.setPixmap(iconPixmap)

    def setUnderline(self, shouldUnderline):
        if shouldUnderline:
            self.setStyleSheet("QWidget#accountSummaryCardContainer{border-bottom: 1px solid #E8E8E8;}")
        else:
            self.setStyleSheet("QWidget#accountSummaryCardContainer{border-bottom: none;}")
