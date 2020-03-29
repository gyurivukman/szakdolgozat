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
    editPreviousPage = pyqtSignal()

    def __init__(self, *args, **kwargs):
        self.__networkSummaryContentPanel = NetworkSummaryContentPanel()
        super().__init__(*args, **kwargs)

    def _setup(self):
        layout = QVBoxLayout()
        networkSummaryPanel = FirstStartSummaryPanel(contentPanel=self.__networkSummaryContentPanel, targetState=WIZARD_PROGRESS_STATES.NETWORK)
        layout.addWidget(networkSummaryPanel)
        self.setLayout(layout)

    def _getStyle(self):
        return "QLabel{border:1px solid red;}"

    def canProceed(self):
        return False

    def canGoBack(self):
        return True

    def setSummaryData(self, summary):
        print(summary)
        self.__networkSummaryContentPanel.setData(summary.network)


class FirstStartSummaryPanel(QWidget, SetupableComponent):

    def __init__(self, *args, **kwargs):
        contentPanel = kwargs.pop("contentPanel")
        self._editButtonTargetState = kwargs.pop("targetState")
        super().__init__(*args, **kwargs)
        self._editButton = None
        self.setObjectName("self")
        self.setStyleSheet(self.__getContainerStyle())
        self.setLayout(self.__createLayout(contentPanel))

    def __getContainerStyle(self):
        return """
            QWidget#self{
                border:2px solid red;
            }
        """

    def __createLayout(self, contentPanel):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignTop|Qt.AlignHCenter)
        layout.setContentsMargins(5, 5, 5, 5)

        self._editButton = QPushButton("EDIT")
        self._editButton.clicked.connect(self._onEditButtonClicked)

        contentPanel.setFixedSize(720, 240)

        layout.addWidget(contentPanel)
        layout.addWidget(self._editButton)

        return layout

    def _onEditButtonClicked(self):
        print(f"GOING TO STATE: {self._editButtonTargetState}")


class NetworkSummaryContentPanel(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dataLabelFont = QFont("Nimbus Sans L", 14, QFont.Bold, False)
        self._dataTextFont = QFont("Nimbus Sans L", 14)
        self._setup()

    def _setup(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        hostSummaryLayout = QVBoxLayout()
        remoteHostLayout = QHBoxLayout()
        sshSummaryLayout = QHBoxLayout()

        self.__hostAddressWidget = DataSummaryWidget(dataLabel="Remote host:", dataText="")
        self.__hostPortWidget = DataSummaryWidget(dataLabel="Remote port:", dataText="")
        self.__aesKeyWidget = DataSummaryWidget(dataLabel="Network encryption key:", dataText="")

        remoteHostLayout.addWidget(self.__hostAddressWidget)
        remoteHostLayout.addWidget(self.__hostPortWidget)

        hostSummaryLayout.addLayout(remoteHostLayout)
        hostSummaryLayout.addWidget(self.__aesKeyWidget)

        layout.addLayout(hostSummaryLayout)
        self.setLayout(layout)

    def setData(self, networkData):
        self.__hostAddressWidget.setDataText(networkData.remote.address)
        self.__hostPortWidget.setDataText(networkData.remote.port)
        self.__aesKeyWidget.setDataText(networkData.remote.encryptionKey)


class DataSummaryWidget(QWidget):

    def __init__(self, *args, **kwargs):
        self.__label = QLabel(kwargs.pop("dataLabel"))
        self.__dataText = QLabel(kwargs.pop("dataText"))

        super().__init__(*args, **kwargs)
        self.setLayout(self.__createLayout())

    def __createLayout(self):
        layout = QHBoxLayout()

        layout.addWidget(self.__label)
        layout.addSpacing(5)
        layout.addWidget(self.__dataText)

        return layout

    def setDataText(self, text):
        self.__dataText.setText(text)
