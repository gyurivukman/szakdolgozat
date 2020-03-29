from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal

from services.hub import ServiceHub


class FirstStartWizardMiddleWidget(QWidget):

    formValidityChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serviceHub = ServiceHub.getInstance()
        self.setFixedSize(1280, 480)
        self.__setupStylesheet()
        self._setup()

    def __setupStylesheet(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(self._getStyle())

    def _setup(self):
        raise NotImplementedError('Derived class must implement method "_setup"')

    def _getStyle(self):
        raise NotImplementedError('Derived class must implement method "_getStyle". It should return a valid qss stylesheet string.')

    def canProceed(self):
        raise NotImplementedError('Derived class must implement method "canProceed". It should return a bool.')

    def canGoBack(self):
        raise NotImplementedError('Derived class must implement method "canGoBack" it should return a bool.')

    def initData(self):
        pass
