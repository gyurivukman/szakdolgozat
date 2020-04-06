import logging
from uuid import uuid4


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QSettings, pyqtSignal, pyqtSlot

from services.hub import ServiceHub
from model.message import MessageTypes, NetworkMessage

from . import resources


moduleLogger = logging.getLogger(__name__)


class MainPanel(QWidget):
    ready = pyqtSignal()

    __fileWidgets = {}
    __serviceHub = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__serviceHub = ServiceHub.getInstance()
        self.__logger = moduleLogger.getChild("MainPanel")

        self.setLayout(self.__createLayout())

    def __createLayout(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(QLabel("MAINPANEL PLACEHOLDER"))

        return layout

    def syncFileList(self):
        self.__logger.debug("Syncing file list")
        rawMessage = {"header": {"messageType": MessageTypes.SYNC_FILES, "uuid": uuid4().hex}, "data": {}}
        message = NetworkMessage(rawMessage)

        self.__serviceHub.sendNetworkMessage(message, self.__onFilelistRetrieved)

    def __onFilelistRetrieved(self, rawFileList):
        self.__logger.debug(f"Retrieved file list: {rawFileList}")
        self.ready.emit()
