from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

from .iconsizes import IconSizes
from . import resources


class WarningPanel(QWidget):

    def __init__(self, text="", iconSize=IconSizes.NORMAL):
        super().__init__()
        self._textLabel = QLabel(text)

        layout = self._createLayout()
        layout.addWidget(QLabel("KUKKEN TOSZ"))
        self.setLayout(layout)

    def _createLayout(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        iconLayout = self._createIconLayout()
        textLayout = self._createTextLayout()

        layout.addLayout(iconLayout)
        layout.addWidget(self._textLabel)

        return layout

    def _createIconLayout(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)

        iconLabel = QLabel()
        iconPixMap = QPixmap(":warning.png").scaled(IconSizes.NORMAL, IconSizes.NORMAL, Qt.IgnoreAspectRatio)
        iconLabel.setPixmap(iconPixMap)

        layout.addWidget(iconLabel)

        return layout

    def _createTextLayout(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self._textLabel)

        return layout


class ConnectionErrorPanel(QWidget):
    retry = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(self._createStylesheet())
        layout = self._createLayout()
        self.setLayout(layout)

    def _createStylesheet(self):
        return """
            QPushButton#retryButton {
                background-color:#e36410;
                color:white;
                width:180px;
                border:0px;
                height:30px;
            }
        """

    def _createLayout(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        warningPanel = WarningPanel("Couldn't connect to the remote server.")
        buttonLayout = QHBoxLayout()
        buttonLayout.setAlignment(Qt.AlignHCenter)
        buttonLayout.setSpacing(25)
        retryButton = QPushButton("Retry")
        retryButton.setObjectName("retryButton")

        retryButton.clicked.connect(self._onRetryClicked)

        buttonLayout.addWidget(retryButton)

        layout.addWidget(warningPanel)
        layout.addLayout(buttonLayout)

        return layout

    def _onRetryClicked(self, _):
        self.retry.emit()
