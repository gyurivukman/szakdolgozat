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
        super().__init__(*args, **kwargs)

    def _setup(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        networkSummaryPanel = FirstStartSummaryPanel(headerText="Network configuration", contentPanel=self.__networkSummaryContentPanel, targetState=WIZARD_PROGRESS_STATES.NETWORK)
        networkSummaryPanel.editButtonClicked.connect(self.__onEditButtonClicked)
        layout.addWidget(networkSummaryPanel)
        layout.addStretch(1)
        self.setLayout(layout)

    def _getStyle(self):
        return ""

    def canProceed(self):
        return False

    def canGoBack(self):
        return True

    def setSummaryData(self, summary):
        self.__configData = summary
        self.__networkSummaryContentPanel.setData(summary.network)

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
        self.setFixedWidth(720)
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
        contentPanel.setFixedWidth(690)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.setContentsMargins(15, 15, 0, 15)

        panelHeaderLayout = QHBoxLayout()
        panelHeaderLayout.setAlignment(Qt.AlignLeft)
        panelHeaderLayout.setSpacing(10)

        headerLabel = QLabel(headerText)
        headerLabel.setFont(QFont("Nimbus Sans L", 16, QFont.Bold, False))

        self._editButton = QPushButton("Edit")
        self._editButton.setObjectName("summaryEditButton")
        self._editButton.setFocusPolicy(Qt.NoFocus)
        self._editButton.clicked.connect(self._onEditButtonClicked)

        panelHeaderLayout.addWidget(headerLabel)
        panelHeaderLayout.addWidget(self._editButton)

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
        raise NotImplementedError("Implement _getStyleSheet!")


class NetworkSummaryContentPanel(SummaryContentPanel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__networkData = None
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

        hostKeyLabel = QLabel("Network Encryption:")
        hostKeyLabel.setFont(self._dataLabelFont)
        self.__hostKeyDataText = QLabel("")
        self.__hostKeyDataText.setFont(self._dataTextFont)

        syncDirLabel = QLabel("Network Encryption:")
        syncDirLabel.setFont(self._dataLabelFont)
        self.__syncDirDataText = QLabel("")
        self.__syncDirDataText.setFont(self._dataTextFont)

        labelsLayout.addWidget(hostAddressLabel)
        labelsLayout.addWidget(hostPortLabel)
        labelsLayout.addWidget(hostKeyLabel)
        labelsLayout.addWidget(syncDirLabel)
        labelsLayout.addStretch(1)

        dataTextLayout.addWidget(self.__hostAddressDataText)
        dataTextLayout.addWidget(self.__hostPortDataText)
        dataTextLayout.addWidget(self.__hostKeyDataText)
        dataTextLayout.addWidget(self.__syncDirDataText)
        dataTextLayout.addStretch(1)

        layout.addLayout(labelsLayout)
        layout.addLayout(dataTextLayout)

        self.setLayout(layout)

    def setData(self, networkData):
        self.__networkData = networkData
        self.__hostAddressDataText.setText(networkData.remote.address)
        self.__hostPortDataText.setText(networkData.remote.port)
        self.__hostKeyDataText.setText(networkData.remote.encryptionKey)
        self.__syncDirDataText.setText(networkData.syncDir)
