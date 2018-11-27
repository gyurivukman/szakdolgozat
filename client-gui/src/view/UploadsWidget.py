import os

from PyQt4 import QtGui, QtCore

from ItemSheet import ItemSheet
from src.controller.ContextManager import ContextManager


class UploadsWidget(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(UploadsWidget, self).__init__(*args, **kwargs)
        self.taskManager = (ContextManager()).getTaskManager()
        self.__setupOwnLayout()
        self.setFixedSize(400, 400)
        self.setAcceptDrops(True)

        self.__setupScrollArea()
        self.__setupScrollContentContainer()
        self.__addItems()

    def __setupOwnLayout(self):
        self.ownLayout = QtGui.QVBoxLayout(self)
        self.setLayout(self.ownLayout)

    def __setupScrollArea(self):
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.ownLayout.addWidget(self.scrollArea)

    def __setupScrollContentContainer(self):
        self.spacer = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.scrollContentContainer = QtGui.QWidget(self.scrollArea)
        self.scrollLayout = QtGui.QVBoxLayout(self.scrollContentContainer)
        self.scrollContentContainer.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollContentContainer)

    def __addItems(self):
        for item in range(15):
            self.scrollLayout.addWidget(
                ItemSheet(self.scrollContentContainer, QtCore.Qt.WindowFlags(0), str(item), 0)
            )
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(0)
        self.scrollLayout.addItem(self.spacer)

    def __handleDropData(self, path):
        if os.path.isdir(path):
            self.__handleDirectoryPath(path)
        elif os.path.isfile(path):
            self.scrollLayout.addWidget(ItemSheet(self.scrollContentContainer, QtCore.Qt.WindowFlags(0), unicode(path), 0))

    def __handleDirectoryPath(self, path):
        for root, dirs, files in os.walk(path):
            for file in files:
                fullPath = os.path.join(root, file)
                self.scrollLayout.addWidget(ItemSheet(self.scrollContentContainer, QtCore.Qt.WindowFlags(0), unicode(fullPath), 0))

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.scrollLayout.removeItem(self.spacer)
            for url in event.mimeData().urls():
                self.__handleDropData(unicode(url.path()).lstrip('/'))
            self.scrollLayout.addItem(self.spacer)
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
