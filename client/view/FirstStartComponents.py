from enum import IntEnum

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit, QRadioButton
from PyQt5.QtCore import QSettings, Qt, pyqtSlot, pyqtSignal
from PyQt5 import QtCore
from PyQt5.QtGui import QColor, QPainter, QFont, QPen, QPixmap, QFontMetrics


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
                QPushButton {
                    background-color:#e36410;
                    color:white;
                    width:150px;
                    border:0px;
                    height:30px;
                }
                QPushButton:disabled {
                    background-color:#D8D8D8;
                }
                QPushButton:pressed {
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
        self.__previousButton = QPushButton("Back")
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
        self.__stageLabelFont = QFont('Arial', 12, QFont.Bold, False)
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
            posY = 20
            width = 80
            height = 80
            if state <= self.__state:
                pen.setColor(self.__activeStateColor)
            else:
                pen.setColor(self.__inactiveStateColor)
            painter.setPen(pen)
            painter.setFont(self.__stageIndexFont)
            painter.drawRect(posX, posY, width, height)
            painter.drawText(QtCore.QRect(posX, posY, width, height), Qt.AlignCenter, str(state.value + 1))
            painter.setFont(self.__stageLabelFont)
            painter.drawText(QtCore.QRect(posX, posY + 90, width, 25), Qt.AlignCenter, state.toDisplayValue())
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
            ENUM_DISPLAY_VALUES = ['Welcome', 'Network', 'Accounts', 'Summary']
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
        return "QWidget#welcomeWidget{background-image:url(./view/assets/encryptionBackground.png);background-repeat:no-repeat;background-position:center;}"


class SetupNetworkWidget(FirstStartWizardMiddleWidget):

    def canProceed(self):
        return self.__isConnectionOK and self.__isSshOK

    def canGoBack(self):
        return True

    def _getStyle(self):
        return """
            QLineEdit {border:1px solid #E39910;}
            QLineEdit:focus {border:2px solid #E39910}
            QLineEdit:hover {border:2px solid #E39910}

            QLineEdit#hostName {max-width: 500px; height:25px; margin-right:20px;}
            QLineEdit#hostPort {max-width: 80px; height:25px; margin-right:40px;}
            QPushButton#testConnection {width: 150px; max-width:150px; border:0; height:25px; margin-right:20px; background-color:#e36410; color:white;}
            QPushButton#testConnection:pressed {background-color:#e68a4e;}

            QLineEdit#sshUsername{max-width: 290px;height:25px;margin-right:20px;}
            QLineEdit#sshPassword{max-width: 290px;height:25px;margin-right:40px;}
            QPushButton#testSSH {width: 150px; max-width:150px; border:0; height:25px; margin-right:20px; background-color:#e36410; color:white;}
            QPushButton#testSSH:pressed {background-color:#e68a4e;}
        """

    def _setup(self):
        self.__formLabelFont = QFont("Helvetica", 14)
        self.__descriptionFont = QFont("Helvetica", 10)
        self.__formInputFont = QFont("Helvetica", 12)

        self.__isConnectionOK = False
        self.__isSshOK = False

        self.__network_data = {"remote": {"address": None, "port": None}, "ssh":{"username": None, "password": None}}

        layout = QVBoxLayout()

        hostLayout = self.__setupHostLayout()
        sshLayout = self.__setupSSHLayout()
        layout.addLayout(hostLayout)
        layout.addLayout(sshLayout)
        layout.setAlignment(Qt.AlignHCenter)
        layout.setContentsMargins(100, 50, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)

        self.setLayout(layout)

    def __setupHostLayout(self):
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
        self.__remoteHostNameInput.textChanged.connect(self.__onFormChanged)
        remoteHostNameInputLayout.addWidget(remoteHostNameLabel)
        remoteHostNameInputLayout.addWidget(self.__remoteHostNameInput)

        remoteHostPortLabel = QLabel("Port")
        remoteHostPortLabel.setFont(self.__formLabelFont)
        self.__remotePortInput = QLineEdit()
        self.__remotePortInput.setObjectName("hostPort")
        self.__remotePortInput.setFont(self.__formInputFont)
        self.__remotePortInput.textChanged.connect(self.__onFormChanged)
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

    def __setupSSHLayout(self):
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
        self.__sshUsernameInput.textChanged.connect(self.__onFormChanged)
        sshFormUsernameInputLayout.addWidget(sshUsernameLabel)
        sshFormUsernameInputLayout.addWidget(self.__sshUsernameInput)

        sshPasswordLabel = QLabel("SSH Password")
        sshPasswordLabel.setFont(self.__formLabelFont)
        self.__sshPasswordInput = QLineEdit()
        self.__sshPasswordInput.setObjectName("sshPassword")
        self.__sshPasswordInput.setFont(self.__formInputFont)
        self.__sshPasswordInput.textChanged.connect(self.__onFormChanged)
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

        sshDescriptionLabel = QLabel("SSH Username and password. CryptStorePi uses SSH to upload and download\nyour files to and from the CryptStorePi encryption server.")
        sshDescriptionLabel.setFont(self.__descriptionFont)
        sshDescriptionLabel.setAlignment(Qt.AlignBottom)
        sshFormLayout.addWidget(sshDescriptionLabel)

        sshLayout.addLayout(sshFormLayout)
        sshLayout.addLayout(sshFormTestConnectionLayout)
        sshLayout.setContentsMargins(0, 40, 0, 0)
        return sshLayout

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

    def __onFormChanged(self):
        self.__isSshOK = False
        self.__isConnectionOK = False
        self.__SSHTestResultLabel.setText("")
        self.__remoteHostTestResultLabel.setText("")
        self.formValidityChanged.emit()


class SetupAccountsWidget(FirstStartWizardMiddleWidget):

    def canProceed(self):
        return len(self.__formData) > 0

    def canGoBack(self):
        return True

    def _getStyle(self):
        return ""

    def _setup(self):
        self.__setupMembers()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # layout.addLayout(self.__createEditorLayout())
        layout.addWidget(AccountEditorWidget())
        layout.addLayout(self.__createAccountListLayout())
        self.setLayout(layout)

    def __setupMembers(self):
        self.__formData = []

    def __createEditorLayout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("EDITOR"))
        layout.addStretch(1)
        return layout

    def __createAccountListLayout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("ACC LIST"))
        layout.addStretch(1)
        return layout


class AccountEditorWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__setup()
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(
            """
                QRadioButton{border-width:2px; border-style:solid; border-radius:3px;}
                QRadioButton::indicator{display:none}
                QRadioButton::checked{border-color: #E39910;}
                QRadioButton::unchecked{border-color: #777777;}
            """
        )

    def __setup(self):
        layout = QVBoxLayout()
        layout.addWidget(AccountEditorSectionSeparatorWidget(sectionName="Account Type"))

        accountTypeLayout = QHBoxLayout()
        self.__dropBoxButton = QRadioButton("Dropbox")
        self.__dropBoxButton.setFixedSize(150, 100)
        self.__dropBoxButton.setChecked(True)
        self.__driveButton = QRadioButton("Google Drive")
        self.__driveButton.setFixedSize(150, 100)
        accountTypeLayout.addWidget(self.__dropBoxButton)
        accountTypeLayout.addWidget(self.__driveButton)
        layout.addLayout(accountTypeLayout)
        layout.addStretch(1)
        self.setLayout(layout)


class AccountEditorSectionSeparatorWidget(QWidget):

    def __init__(self, *args, **kwargs):
        self.__sectionText = kwargs.pop("sectionName")
        self.__sectionFont = QFont(QFont('Helvetica', 12, QFont.Bold))
        self.__sectionFontMetrics = QFontMetrics(self.__sectionFont)
        super().__init__(*args, **kwargs)
        self.setFixedSize(960, 25)

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.__drawWidget(qp)
        qp.end()

    def __drawWidget(self, painter):
        width = self.__sectionFontMetrics.width(self.__sectionText)
        height = self.__sectionFontMetrics.height()

        painter.setFont(self.__sectionFont)
        painter.setPen(QPen(QColor("#888888"), 1, Qt.SolidLine))
        painter.drawText(QtCore.QRect(480 - (width / 2), 0, width, height), Qt.AlignCenter, self.__sectionText)
        painter.drawLine(50, (height / 2) + 1, 480 - (width / 2 + 5), (height / 2) + 1)
        painter.drawLine(485 + (width / 2), (height / 2) + 1, 910, (height / 2) + 1)


class AccountListWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(320, 480)
        self.__setup()

    def __setup(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Account List PLaceholder"))
        self.setLayout(layout)
