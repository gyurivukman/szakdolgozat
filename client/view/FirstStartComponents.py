from enum import IntEnum

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import QSettings, Qt
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
        self.__setup()

    def __setup(self):
        self.__layout = QVBoxLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__progressWidget = WizardProgressWidget()
        self.__welcomeWidget = WelcomeWidget()
        self.__layout.addWidget(self.__progressWidget, 0, Qt.AlignTop)
        self.__layout.addWidget(self.__welcomeWidget, 0, Qt.AlignTop)
        self.__layout.addStretch(1)
        self.setLayout(self.__layout)


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
        self.__ENUM_DISPLAY_VALUES = ['Welcome', 'Setup SSH', 'Accounts', 'Summary']
        self.__activeStateColor = QColor('#E39910')
        self.__inactiveStateColor = QColor('#D8D8D8')
        self.__separatorLineColor = QColor('#777777')
        self.__stageIndexFont = QFont('Arial', 32, QFont.Bold, False)
        self.__stageLabelFont = QFont('Arial', 12, QFont.Bold, False)
        self.__pen = QPen(self.__activeStateColor, 6, Qt.SolidLine)
        self.setFixedSize(1280, 160)
        # self.setAttribute(Qt.WA_StyledBackground)
        # self.setStyleSheet("background:#151515;")

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.__drawWidget(qp)
        qp.end()

    def __drawWidget(self, painter):
        self.__drawProgressIcons(painter)
        self.__drawSeparatorLine(painter)

    def __drawProgressIcons(self, painter):
        for state in self.WIZARD_PROGRESS_STATES:
            posX = (state.value * 320) + 120
            posY = 20
            width = 80
            height = 80
            if state <= self.__state:
                self.__pen.setColor(self.__activeStateColor)
            else:
                self.__pen.setColor(self.__inactiveStateColor)
            painter.setPen(self.__pen)
            painter.setFont(self.__stageIndexFont)
            painter.drawRect(posX, posY, width, height)
            painter.drawText(QtCore.QRect(posX, posY, width, height), Qt.AlignCenter, str(state.value + 1))
            painter.setFont(self.__stageLabelFont)
            painter.drawText(QtCore.QRect(posX, posY + 90, width, 25), Qt.AlignCenter, self.__ENUM_DISPLAY_VALUES[state.value])
            if state > self.WIZARD_PROGRESS_STATES.WELCOME:
                painter.drawLine(posX - 6, posY + (height / 2), posX - 234, posY + (height / 2))

    def __drawSeparatorLine(self, painter):
        self.__pen.setColor(self.__inactiveStateColor)
        self.__pen.setWidth(1)
        painter.setPen(self.__pen)
        painter.drawLine(10, 159, 1270, 159)

    def toNextState(self):
        self.__state = self.__state.next()
        #TODO return new state

    def toPreviousState(self):
        self.__state = self.__state.previous()
        #TODO return new state

    class WIZARD_PROGRESS_STATES(IntEnum):
        WELCOME = 0
        SETUP_SSH = 1
        SETUP_ACCOUNTS = 2
        SUMMARY = 3

        def next(self):
            if self.value == 3:
                raise ValueError('Enumeration ended')
            return WIZARD_PROGRESS_STATES(self.value + 1)

        def previous(self):
            if self.value == 0:
                raise ValueError('Enumeration ended')
            return WIZARD_PROGRESS_STATES(self.value - 1)


class WelcomeWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background-image: url(./view/assets/Presentation1.png);background-repeat:no-repeat;background-position:center")
        self.__setup()

    def __setup(self):
        self.setFixedSize(1280, 480)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 50, 0, 0)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignTop)
        welcomeLabel = QLabel("Welcome to CryptStorePi!")
        welcomeLabelFont = QFont('Arial', 42, QFont.Normal)
        welcomeLabelFont.setUnderline(True)
        welcomeLabel.setFont(welcomeLabelFont)
        welcomeInstructionsLabel = QLabel("This wizard will guide you through the first setup of this application.")
        welcomeInstructionsLabel.setFont(QFont('Arial', 22, QFont.Normal))
        continueInstructionLabel = QLabel("To start, click 'Next'!")
        continueInstructionLabel.setFont(QFont('Arial', 16, QFont.Normal))

        layout.addWidget(welcomeLabel, 0, Qt.AlignHCenter)
        layout.addWidget(welcomeInstructionsLabel, 0, Qt.AlignHCenter)
        layout.addWidget(continueInstructionLabel, 0, Qt.AlignHCenter)
        self.setLayout(layout)

