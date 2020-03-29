from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton
)

from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon

from model.config import AccountData, AccountTypes
from view import resources
from view.firststart.abstract import FirstStartWizardMiddleWidget


class FirstStartSummaryWidget(FirstStartWizardMiddleWidget):

    def _setup(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("I AM THE SUMMARY"))
        self.setLayout(layout)

    def _getStyle(self):
        return "QLabel{border:1px solid red;}"

    def canProceed(self):
        return False

    def canGoBack(self):
        return True

    def setSummaryData(self, summary):
        print(summary)
