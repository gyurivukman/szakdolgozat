from enum import IntEnum

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt

class LoadingWidget(QWidget):

    class LoaderSizes(IntEnum):
        SMALL = 50
        NORMAL = 100
        LARGE = 200

    def __init__(self, size=LoaderSizes.NORMAL):
        super().__init__()
        self.setFixedSize(size, size)
        self.__setup(size)

    def __setup(self, size):
        layout = QVBoxLayout()
        svgWidget = QSvgWidget('./view/assets/loader.svg')
        svgWidget.setFixedSize(size, size)
        layout.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        layout.addWidget(svgWidget)

        self.setLayout(layout)
