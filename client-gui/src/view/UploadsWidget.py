import os
from PyQt4 import QtGui, QtCore

from ItemSheet import ItemSheet
from src.controller.ContextManager import ContextManager
from src.model.Task import TaskTypes


class UploadsWidget(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(UploadsWidget, self).__init__(*args, **kwargs)

        self.__setup()        
        self.__setupScrollArea()
        self.__setupScrollContentContainer()

    def __setup(self):
        self.__taskManager = (ContextManager()).getTaskManager()
        self.__taskManager.fileStatusChannel.connect(self.__onFileStatusChange)
        self.__itemSheets = {}
        self.__setupOwnLayout()
        self.setFixedSize(500, 400)
        self.setAcceptDrops(True)

    def __setupOwnLayout(self):
        self.ownLayout = QtGui.QVBoxLayout(self)
        self.setLayout(self.ownLayout)

    def __setupScrollArea(self):
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.ownLayout.addWidget(self.scrollArea)

    def __setupScrollContentContainer(self):
        self.__spacer = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.scrollContentContainer = QtGui.QWidget(self.scrollArea)
        self.__scrollLayout = QtGui.QVBoxLayout(self.scrollContentContainer)
        self.__scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.__scrollLayout.setSpacing(0)
        self.__scrollLayout.addItem(self.__spacer)
        self.scrollContentContainer.setLayout(self.__scrollLayout)
        self.scrollArea.setWidget(self.scrollContentContainer)

    def __handleDropData(self, path):
        if os.path.isdir(path):
            self.__handleDirectoryPath(path)
        elif os.path.isfile(path):
            self.__scrollLayout.addWidget(ItemSheet(self.scrollContentContainer, QtCore.Qt.WindowFlags(0), unicode(path), 0))

    def __handleDirectoryPath(self, path):
        for root, dirs, files in os.walk(path):
            for file in files:
                fullPath = os.path.join(root, file)
                self.__scrollLayout.addWidget(ItemSheet(self.scrollContentContainer, QtCore.Qt.WindowFlags(0), unicode(fullPath), 0))

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.__scrollLayout.removeItem(self.__spacer)
            for url in event.mimeData().urls():
                self.__handleDropData(unicode(url.path()).lstrip('/'))
            self.__scrollLayout.addItem(self.__spacer)
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def __onFileStatusChange(self, task):
        relativePath = task.subject["dir"] + '/' + task.subject["fileName"] if task.subject["dir"] !="" else task.subject["fileName"]
        if relativePath not in self.__itemSheets:
            itemSheet = ItemSheet(self.scrollContentContainer, QtCore.Qt.WindowFlags(0), task.subject, task.status)
            self.__itemSheets[relativePath] = itemSheet
            self.__scrollLayout.removeItem(self.__spacer)
            self.__scrollLayout.addWidget(itemSheet)
        else:
            if task.taskType == TaskTypes.DELETEFILE:
                self.__scrollLayout.removeItem(self.__itemSheets[relativePath])
            else:
                (self.__itemSheets[relativePath]).updateStatus(task.status)
        self.__scrollLayout.removeItem(self.__spacer)
        self.__scrollLayout.addItem(self.__spacer)
            # elif task.taskType == TaskTypes.MOVE_FILE:
