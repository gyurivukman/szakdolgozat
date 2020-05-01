import logging
from uuid import uuid4


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QLayout
from PyQt5.QtCore import Qt, QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap

from services.hub import ServiceHub
from model.message import MessageTypes, NetworkMessage
from model.file import FileData, FileStatuses, FileStatusEvent, FileEventTypes

from . import resources


moduleLogger = logging.getLogger(__name__)


class FileTrackerIconAtlas:

    def __init__(self):
        self.cloudUploadIcon = QPixmap(":cloud_upload.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.cloudDownloadIcon = QPixmap(":cloud_download.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.diskUploadIcon = QPixmap(":disk_upload.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.diskDownloadIcon = QPixmap(":disk_download.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.syncedIcon = QPixmap(":check.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.encryptingIcon = QPixmap(":encrypting.png").scaled(20, 20, Qt.IgnoreAspectRatio)
        self.movingIcon = QPixmap(":move.png").scaled(20, 20, Qt.IgnoreAspectRatio)

        self.__stateMap = {
            FileStatuses.SYNCED: self.syncedIcon,
            FileStatuses.UPLOADING_FROM_LOCAL: self.diskUploadIcon,
            FileStatuses.DOWNLOADING_TO_LOCAL: self.diskDownloadIcon,
            FileStatuses.UPLOADING_TO_CLOUD: self.cloudUploadIcon,
            FileStatuses.DOWNLOADING_FROM_CLOUD: self.cloudDownloadIcon,
            FileStatuses.MOVING: self.movingIcon
        }

    def fromFileState(self, state):
        try:
            return self.__stateMap[state]
        except KeyError:
            raise Exception(f"'{state}' is not a valid state!")


class MainPanel(QWidget):
    ready = pyqtSignal()

    __fileWidgets = {}
    __serviceHub = None
    __stateSuccessionMap = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.__serviceHub = ServiceHub.getInstance()
        self.__serviceHub.filesChannel.connect(self.__onFileStatusEvent)
        self.__stateSuccessionMap = self.__createStateSuccessionMap()

        self.__fileTrackerIconAtlas = FileTrackerIconAtlas()
        self.__logger = moduleLogger.getChild("MainPanel")
        self.__filesLayout = self.__createFilesLayout()

        scrollableContainerWidget = self.__createScrollableContainerWidget(self.__filesLayout)
        scroll = self.__createScrollArea()
        scroll.setWidget(scrollableContainerWidget)

        layout = QHBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)
        self.setStyleSheet(
            """
                QScrollArea, QWidget#scrollContainer{background-color:white;margin:0px;}
                QScrollArea {border:1px solid #E36410;}

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
        scroll.setWidgetResizable(True)

        return scroll

    def __createFilesLayout(self):
        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignHCenter)
        layout.addStretch(1)

        return layout

    def __createStateSuccessionMap(self):
        successionMap = {
            FileStatuses.DOWNLOADING_FROM_CLOUD: [FileStatuses.UPLOADING_FROM_LOCAL, FileStatuses.MOVING, FileStatuses.DOWNLOADING_TO_LOCAL, FileStatuses.DELETED],
            FileStatuses.UPLOADING_TO_CLOUD: [FileStatuses.SYNCED, FileStatuses.UPLOADING_FROM_LOCAL, FileStatuses.MOVING, FileStatuses.DELETED],
            FileStatuses.DOWNLOADING_TO_LOCAL: [FileStatuses.SYNCED, FileStatuses.UPLOADING_FROM_LOCAL, FileStatuses.MOVING, FileStatuses.DELETED],
            FileStatuses.UPLOADING_FROM_LOCAL: [FileStatuses.UPLOADING_FROM_LOCAL, FileStatuses.UPLOADING_TO_CLOUD, FileStatuses.MOVING, FileStatuses.DELETED],
            FileStatuses.SYNCED: [FileStatuses.UPLOADING_FROM_LOCAL, FileStatuses.MOVING, FileStatuses.DELETED],
            FileStatuses.MOVING: [FileStatuses.UPLOADING_FROM_LOCAL, FileStatuses.MOVING, FileStatuses.DELETED, FileStatuses.SYNCED]
        }

        return successionMap

    def syncFileList(self):
        self.__logger.debug("Syncing file list")
        message = NetworkMessage.Builder(MessageTypes.SYNC_FILES).withRandomUUID().build()

        self.__serviceHub.sendNetworkMessage(message, self.__onFilelistRetrieved)

    def __onFilelistRetrieved(self, rawFileList):
        serializedFileList = [FileData(**raw) for raw in rawFileList]
        self.__serviceHub.syncRemoteAndLocalFiles(serializedFileList)
        # TODO újrakonfirmálni hogy fut-e a filesyncer first startnál és nem first startnál!
        self.ready.emit()

    @pyqtSlot(FileStatusEvent)
    def __onFileStatusEvent(self, event):
        self.__logger.debug(f"Received event: {event}")
        if event.eventType == FileEventTypes.CREATED:
            fileTrackerWidget = FileTrackerWidget(fullPath=event.sourcePath, status=event.status, iconAtlas=self.__fileTrackerIconAtlas)
            self.__fileWidgets[event.sourcePath] = fileTrackerWidget
            self.__filesLayout.insertWidget(self.__filesLayout.count() - 1, fileTrackerWidget)
        elif event.eventType == FileEventTypes.STATUS_CHANGED:
            if event.sourcePath in self.__fileWidgets and event.status in self.__stateSuccessionMap[self.__fileWidgets[event.sourcePath].getStatus()]:
                self.__fileWidgets[event.sourcePath].setStatus(event.status)
            else:
                self.__logger.warning(f"Invalid status transition: {event}. Ignoring.")
        elif event.eventType == FileEventTypes.MODIFIED:
            self.__fileWidgets[event.sourcePath].setStatus(event.status)
        elif event.eventType == FileEventTypes.DELETED:
            self.__fileWidgets[event.sourcePath].setParent(None)
            del self.__fileWidgets[event.sourcePath]
        elif event.eventType == FileEventTypes.MOVED:
            if event.destinationPath in self.__fileWidgets:
                self.__fileWidgets[event.destinationPath].setParent(None)
                del self.__fileWidgets[event.destinationPath]
            self.__fileWidgets[event.destinationPath] = self.__fileWidgets[event.sourcePath]
            self.__fileWidgets[event.destinationPath].setFullPath(event.destinationPath)
            self.__fileWidgets[event.destinationPath].setStatus(event.status)
            del self.__fileWidgets[event.sourcePath]
        else:
            self.__logger.debug(f"Unknown event in MainPanel: {event}")


class FileTrackerWidget(QWidget):
    __statusDisplayValues = ["Downloading from cloud", "Uploading to cloud", "Downloading from remote", "Uploading to remote", "Synchronized", "Moving/renaming"]

    def __init__(self, *args, **kwargs):
        self.__fileTrackerIconAtlas = kwargs.pop("iconAtlas")
        fullPath = kwargs.pop("fullPath")
        self.__status = kwargs.pop("status")

        super().__init__(*args, **kwargs)

        self.__fileLabel = QLabel(fullPath)
        self.__statusLabel = QLabel(self.__displayValueOfStatus(self.__status))
        self.__statusIcon = QLabel()
        self.__statusIcon.setPixmap(self.__fileTrackerIconAtlas.fromFileState(self.__status))

        self.setLayout(self.__createLayout())
        self.setStyleSheet("QWidget#fileTrackerContainerWidget{border:2px solid #E36410;}")

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

    def setFullPath(self, fullPath):
        self.__fileLabel.setText(fullPath)

    def getStatus(self):
        return self.__status

    def setStatus(self, status):
        self.__status = status
        self.__statusLabel.setText(self.__statusDisplayValues[status])
        self.__statusIcon.setPixmap(self.__fileTrackerIconAtlas.fromFileState(status))

    def __displayValueOfStatus(self, status):
        return self.__statusDisplayValues[status]
