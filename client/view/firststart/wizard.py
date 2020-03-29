from enum import IntEnum

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import QSettings, Qt, QRect
from PyQt5.QtGui import QColor, QPainter, QFont, QPen

from model.config import FirstStartConfig
from model.wizard import WIZARD_PROGRESS_STATES
from view.firststart.welcome import WelcomeWidget
from view.firststart.network import SetupNetworkWidget
from view.firststart.accounts import SetupAccountsWrapperWidget
from view.firststart.summary import FirstStartSummaryWidget


class FirstStartWizard(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__settings = QSettings()
        self.__widgetMap = self.__createWidgetMap()
        self.__setup()

    def __createWidgetMap(self):
        widgetMap = {
            WIZARD_PROGRESS_STATES.WELCOME: WelcomeWidget()
        }

        setupNetworkWidget = SetupNetworkWidget()
        setupNetworkWidget.formValidityChanged.connect(self.__checkCanProceed)
        widgetMap[WIZARD_PROGRESS_STATES.NETWORK] = setupNetworkWidget

        setupAccountsWidget = SetupAccountsWrapperWidget()
        setupAccountsWidget.formValidityChanged.connect(self.__checkCanProceed)
        widgetMap[WIZARD_PROGRESS_STATES.ACCOUNTS] = setupAccountsWidget

        summaryWidget = FirstStartSummaryWidget()
        summaryWidget.editPreviousPage.connect(self.__onSummaryEditClicked)
        widgetMap[WIZARD_PROGRESS_STATES.SUMMARY] = summaryWidget

        return widgetMap

    def __checkCanProceed(self):
        canProceed = self.__widgetMap[self.__state].canProceed()
        self.__nextButton.setEnabled(canProceed)
        if self.__state == WIZARD_PROGRESS_STATES.NETWORK and not canProceed:
            accountsWidget = self.__widgetMap[WIZARD_PROGRESS_STATES.ACCOUNTS]
            if accountsWidget.isInited():
                accountsWidget.invalidate()

    def __setup(self):
        self.__state = WIZARD_PROGRESS_STATES.WELCOME
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
            widget.show() if key == WIZARD_PROGRESS_STATES.WELCOME else widget.hide()
        self.__layout.addStretch(1)

        self.__nextButton = QPushButton("Next")
        self.__nextButton.setObjectName("controlButton")
        self.__nextButton.setFocusPolicy(Qt.NoFocus)
        self.__nextButton.clicked.connect(self.__goNext)
        self.__previousButton = QPushButton("Back")
        self.__previousButton.setObjectName("controlButton")
        self.__previousButton.setDisabled(True)
        self.__previousButton.clicked.connect(self.__goBack)
        self.__previousButton.setFocusPolicy(Qt.NoFocus)
        self.__finishButton = QPushButton("Finish")
        self.__finishButton.setObjectName("controlButton")
        self.__finishButton.clicked.connect(self.__onFinishClicked)
        self.__finishButton.setFocusPolicy(Qt.NoFocus)
        self.__finishButton.hide()

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 10, 10)
        controlLayout.setSpacing(20)
        controlLayout.setAlignment(Qt.AlignTrailing)
        controlLayout.addWidget(self.__previousButton)
        controlLayout.addWidget(self.__nextButton)
        controlLayout.addWidget(self.__finishButton)

        self.__layout.addLayout(controlLayout)
        self.setLayout(self.__layout)

    def __goNext(self):
        self.__widgetMap[self.__state].hide()
        self.__state = self.__progressWidget.toNextState()
        self.__widgetMap[self.__state].show()
        if self.__state == WIZARD_PROGRESS_STATES.ACCOUNTS and not self.__widgetMap[WIZARD_PROGRESS_STATES.ACCOUNTS].isInited():
            self.__widgetMap[self.__state].initData()
        elif self.__state == WIZARD_PROGRESS_STATES.SUMMARY:
            self.__widgetMap[self.__state].setSummaryData(self.__gatherFormData())
        self.__update()

    def __goBack(self):
        self.__widgetMap[self.__state].hide()
        self.__state = self.__progressWidget.toPreviousState()
        self.__widgetMap[self.__state].show()
        self.__update()

    def __gatherFormData(self):
        networkConfig = self.__widgetMap[WIZARD_PROGRESS_STATES.NETWORK].getFormData()
        accounts = self.__widgetMap[WIZARD_PROGRESS_STATES.ACCOUNTS].getFormData()

        return FirstStartConfig(networkConfig, accounts)

    def __update(self):
        if self.__state != WIZARD_PROGRESS_STATES.SUMMARY:
            self.__nextButton.show()
            self.__nextButton.setDisabled(not self.__widgetMap[self.__state].canProceed())
            self.__finishButton.hide()
        else:
            self.__nextButton.hide()
            self.__finishButton.show()
        self.__previousButton.setDisabled(not self.__widgetMap[self.__state].canGoBack())
        self.__progressWidget.update()
        self.update()

    def __onFinishClicked(self):
        print("Finish!")
        config = self.__widgetMap[WIZARD_PROGRESS_STATES.SUMMARY].getConfigData()
        print(config)

    def __jumpToState(self, state):
        self.__widgetMap[self.__state].hide()
        self.__progressWidget.setState(state)
        self.__state = state
        self.__widgetMap[self.__state].show()
        self.__update()

    def __onSummaryEditClicked(self, state):
        state = WIZARD_PROGRESS_STATES(state)
        self.__jumpToState(state)


class WizardProgressWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__state = WIZARD_PROGRESS_STATES.WELCOME
        self.__activeStateColor = QColor('#E39910')
        self.__inactiveStateColor = QColor('#D8D8D8')
        self.__separatorLineColor = QColor('#777777')
        self.__stageIndexFont = QFont('Arial', 32, QFont.Bold, False)
        self.__stageLabelFont = QFont('Arial', 10, QFont.Bold, False)
        self.setFixedSize(1280, 160)

    def paintEvent(self, _):
        qp = QPainter()
        qp.begin(self)
        self.__drawWidget(qp)
        qp.end()

    def __drawWidget(self, painter):
        self.__drawProgressIcons(painter)
        self.__drawSeparatorLine(painter)

    def __drawProgressIcons(self, painter):
        pen = QPen(self.__activeStateColor, 6, Qt.SolidLine)
        for state in WIZARD_PROGRESS_STATES:
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
            if state > WIZARD_PROGRESS_STATES.WELCOME:
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

    def setState(self, state):
        self.__state = state
