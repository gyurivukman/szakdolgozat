from enum import IntEnum

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from . import resources
from PyQt5.QtGui import QColor, QPainter, QFont, QPen, QPixmap, QFontMetrics, QIcon
from model.iconsizes import IconSizes


class LoaderWidget(QWidget):

    def __init__(self, sizeX, sizeY, statusText="", iconSize=IconSizes.NORMAL):
        super().__init__()
        self.setFixedSize(sizeX, sizeY)
        self._layout = None
        self._statusLabel = None
        self._setupPanel(statusText, iconSize)

    def setStatusText(self, statusText):
        self._statusLabel.setText(statusText)

    def _setupPanel(self, statusText, iconSize):
        self._layout = QVBoxLayout()
        self._layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        iconLayout = self._createIconLayout(iconSize)
        statusLayout = self._createStatusTextLayout(statusText)

        self._layout.addLayout(iconLayout)
        self._layout.addLayout(statusLayout)
        self.setLayout(self._layout)

    def _createIconLayout(self, iconSize):
        iconLayout = QHBoxLayout()
        iconLayout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        svgWidget = QSvgWidget(':loader.svg')
        svgWidget.setFixedSize(iconSize, iconSize)
        iconLayout.addWidget(svgWidget)

        return iconLayout

    def _createStatusTextLayout(self, statusText):
        statusLayout = QHBoxLayout()
        statusLayout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self._statusLabel = QLabel(statusText)
        self._statusLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        statusLayout.addWidget(self._statusLabel)

        return statusLayout
