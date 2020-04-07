import logging
from uuid import uuid4


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QLayout
from PyQt5.QtCore import Qt, QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap

from services.hub import ServiceHub
from model.message import MessageTypes, NetworkMessage
from model.file import FileData

from . import resources


moduleLogger = logging.getLogger(__name__)


class FileTrackerIconAtlas():

    def __init__(self):
        self.cloudUploadIcon = QPixmap(":cloud_upload.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.cloudDownloadIcon = QPixmap(":cloud_download.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.diskUploadIcon = QPixmap(":disk_upload.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.diskDownloadIcon = QPixmap(":cloud_upload.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.syncedIcon = QPixmap(":check.png").scaled(20, 20, Qt.IgnoreAspectRatio)


class MainPanel(QWidget):
    ready = pyqtSignal()

    __fileWidgets = {}
    __serviceHub = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.__serviceHub = ServiceHub.getInstance()
        self.__fileTrackerIconAtlas = FileTrackerIconAtlas()
        self.__logger = moduleLogger.getChild("MainPanel")
        self.__filesLayout = self.__createFilesLayout()
        self.__filesLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.__filesLayout.setContentsMargins(5, 5, 5, 5)

        scrollableContainerWidget = self.__createScrollableContainerWidget(self.__filesLayout)
        scroll = self.__createScrollArea()
        scroll.setWidget(scrollableContainerWidget)

        layout = QHBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)
        self.setStyleSheet(
            """
                QScrollArea, QWidget#scrollContainer{background-color:white;margin:0px;}

                QScrollBar:vertical {
                    background-color: white;
                    width: 16px;
                    margin: 0px 2px 0px 2px;
                    border: 1px solid #E36410;
                    border-radius: 4px;
                }

                QScrollBar::handle:vertical {
                    background-color: #777777;
                    border: none;
                    min-height: 8px;
                    border-radius: 4px;
                }

                QScrollBar::handle:vertical:hover {
                    background-color: #E36410;
                    border-radius: 4px;
                    min-height: 8px;
                }

                QScrollBar::handle:vertical:focus {
                    border: 1px solid #1464A0;
                }

                QScrollBar::add-line:vertical {
                    border-image: none;
                    height: 0px;
                    width: 0px;
                    subcontrol-position: bottom;
                    subcontrol-origin: margin;
                }

                QScrollBar::add-line:vertical:hover, QScrollBar::add-line:vertical:on {
                    border-image: none;
                    height: 0px;
                    width: 0px;
                    subcontrol-position: bottom;
                    subcontrol-origin: margin;
                }

                QScrollBar::sub-line:vertical {
                    border-image: none;
                    height: 0px;
                    width: 0px;
                    subcontrol-position: top;
                    subcontrol-origin: margin;
                }

                QScrollBar::sub-line:vertical:hover, QScrollBar::sub-line:vertical:on {
                    border-image: none;
                    height: 0px;
                    width: 0px;
                    subcontrol-position: top;
                    subcontrol-origin: margin;
                }

                QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                    background: none;
                    height:0px;
                }

                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """
        )

    def __createScrollableContainerWidget(self, layout):
        containerWidget = QWidget()
        containerWidget.setAttribute(Qt.WA_StyledBackground)
        containerWidget.setLayout(layout)
        containerWidget.setObjectName("scrollContainer")

        return containerWidget

    def __createScrollArea(self):
        scroll = QScrollArea()
        scroll.setFixedWidth(460)
        scroll.setFixedHeight(680)
        scroll.setAttribute(Qt.WA_StyledBackground)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(False)

        return scroll

    def __createFilesLayout(self):
        layout = QVBoxLayout()
        layout.addStretch(1)

        return layout

    def syncFileList(self):
        self.__logger.debug("Syncing file list")
        message = NetworkMessage.Builder(MessageTypes.SYNC_FILES).withRandomUUID().build()

        self.__serviceHub.sendNetworkMessage(message, self.__onFilelistRetrieved)

    def __onFilelistRetrieved(self, rawFileList):
        self.__logger.debug(f"Remote files:\n {rawFileList} \n")
        for i in range(30):
            fileWidget = FileTrackerWidget(iconAtlas=self.__fileTrackerIconAtlas)
            self.__filesLayout.insertWidget(i, fileWidget)
        # self.__serviceHub.mergeFilelists()
        self.ready.emit()


class FileTrackerWidget(QWidget):

    def __init__(self, *args, **kwargs):
        self.__fileTrackerIconAtlas = kwargs.pop("iconAtlas")
        super().__init__(*args, **kwargs)
        self.__fileLabel = QLabel("Lorem Ipsum si doloret")
        self.__statusLabel = QLabel("FILE_STATUS_PLACEHOLDER")
        self.__statusIcon = QLabel()
        self.__statusIcon.setPixmap(self.__fileTrackerIconAtlas.cloudUploadIcon)

        self.setLayout(self.__createLayout())
        self.setStyleSheet("QWidget#fileTrackerContainerWidget{border:2px solid #777777;}")

    def __createLayout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        containerWidget = QWidget()
        containerWidget.setFixedSize(430, 55)
        containerWidget.setObjectName("fileTrackerContainerWidget")

        containerLayout = QVBoxLayout()
        containerLayout.setContentsMargins(5, 5, 5, 5)

        fileNameLayout = QHBoxLayout()
        fileNameLayout.setAlignment(Qt.AlignLeft)
        fileNameLayout.addWidget(self.__fileLabel)

        statusLayout = QHBoxLayout()
        statusLayout.setAlignment(Qt.AlignLeft)
        statusLayout.setSpacing(5)
        statusLayout.addWidget(self.__statusIcon)
        statusLayout.addWidget(self.__statusLabel)

        containerLayout.addLayout(fileNameLayout)
        containerLayout.addStretch(1)
        containerLayout.addLayout(statusLayout)

        containerWidget.setLayout(containerLayout)
        layout.addWidget(containerWidget)

        return layout
