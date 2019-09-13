from enum import IntEnum

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import QSettings, Qt, pyqtSlot
from PyQt5 import QtCore
from PyQt5.QtGui import QColor, QPainter, QFont, QPen, QPixmap


class FirstStartWizard(QWidget):
    """
        This is the wizard widget that is being shown if the user hasn't configured the software yet.
        Inherits from QWidget.
        Displays the first start setup widget, the current stage and controls for moving between stages.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__settings = QSettings()
        self.__widgetMap = {
            WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME: WelcomeWidget(),
            WizardProgressWidget.WIZARD_PROGRESS_STATES.NETWORK: SetupNetworkWidget(),
            WizardProgressWidget.WIZARD_PROGRESS_STATES.ACCOUNTS: WelcomeWidget(),
            WizardProgressWidget.WIZARD_PROGRESS_STATES.SUMMARY: SetupNetworkWidget(),
        }
        self.__setup()

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
        """)

    def __setupWidgets(self):
        self.__layout = QVBoxLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__progressWidget = WizardProgressWidget()
        self.__setupNetworkWidget = SetupNetworkWidget()
        self.__layout.addWidget(self.__progressWidget, 0, Qt.AlignTop)

        for key, widget in self.__widgetMap.items():
            self.__layout.addWidget(widget, 0, Qt.AlignTop)
            widget.show() if key == WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME else widget.hide()

        self.__nextButton = QPushButton("Next")
        self.__nextButton.clicked.connect(self.__goNext)
        self.__previousButton = QPushButton("Back")
        self.__previousButton.setDisabled(True)
        self.__previousButton.clicked.connect(self.__goBack)
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 20, 20)
        controlLayout.setSpacing(20)
        controlLayout.setAlignment(Qt.AlignTrailing)
        controlLayout.addWidget(self.__previousButton)
        controlLayout.addWidget(self.__nextButton)

        self.__layout.addLayout(controlLayout)
        self.setLayout(self.__layout)

    @pyqtSlot()
    def __goNext(self):
        if self.__state != WizardProgressWidget.WIZARD_PROGRESS_STATES.SUMMARY:
            self.__previousButton.setDisabled(False)
            self.__widgetMap[self.__state].hide()
            self.__state = self.__progressWidget.toNextState()
            self.__widgetMap[self.__state].show()
            if self.__state == WizardProgressWidget.WIZARD_PROGRESS_STATES.SUMMARY:
                self.__nextButton.setDisabled(True)
            self.__progressWidget.update()
            self.update()

    @pyqtSlot()
    def __goBack(self):
        if self.__state == WizardProgressWidget.WIZARD_PROGRESS_STATES.SUMMARY:
            self.__nextButton.setDisabled(False)
        self.__widgetMap[self.__state].hide()
        self.__state = self.__progressWidget.toPreviousState()
        self.__widgetMap[self.__state].show()
        if self.__state == WizardProgressWidget.WIZARD_PROGRESS_STATES.WELCOME:
            self.__previousButton.setDisabled(True)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background-image:url(./view/assets/Presentation1.png);background-repeat:no-repeat;background-position:center")
        self.setFixedSize(1280, 480)

    def __setup(self):
        raise NotImplementedError('Derived class must implement method "__setup"')


class WelcomeWidget(FirstStartWizardMiddleWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__setup()

    def __setup(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 50, 0, 0)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignTop)

        welcomeLabel = QLabel("Welcome to CryptStorePi!")
        welcomeLabelFont = QFont('Helvetica', 42, QFont.Normal)
        welcomeLabelFont.setUnderline(True)
        welcomeLabel.setFont(welcomeLabelFont)

        welcomeInstructionsLabel = QLabel("This wizard will guide you through the first setup of this application.")
        welcomeInstructionsLabel.setFont(QFont('Helvetica', 22, QFont.Normal))
        continueInstructionLabel = QLabel("To start, click 'Next'!")
        continueInstructionLabel.setFont(QFont('Helvetica', 16, QFont.Normal))

        layout.addWidget(welcomeLabel, 0, Qt.AlignHCenter)
        layout.addWidget(welcomeInstructionsLabel, 0, Qt.AlignHCenter)
        layout.addWidget(continueInstructionLabel, 0, Qt.AlignHCenter)
        self.setLayout(layout)


class SetupNetworkWidget(FirstStartWizardMiddleWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__setup()

    def __setup(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 50, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        headingLabel = QLabel("<h3>Setup network connections</h3>")
        
        layout.addWidget(headingLabel, 0, Qt.AlignHCenter)
        self.setLayout(layout)
