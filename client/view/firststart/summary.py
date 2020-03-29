from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton
)

from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon

from model.config import AccountData, AccountTypes

from view import resources
from view.firststart.abstract import FirstStartWizardMiddleWidget
from view.firststart.abstract import SetupableComponent


class FirstStartSummaryWidget(FirstStartWizardMiddleWidget):
    editPreviousPage = pyqtSignal()

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


class FirstStartSummaryConfigPanel(QWidget, SetupableComponent):

    def __init__(*args, **kwargs):
        self._panelContent = kwargs.pop['panelContent']
        super().__init__(*args, **kwargs)
