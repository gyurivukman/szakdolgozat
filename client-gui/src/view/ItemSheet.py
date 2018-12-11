from PyQt4 import QtCore, QtGui

import src.model.TaskStatus as TaskStatus


class ItemSheet(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(ItemSheet, self).__init__(args[0], args[1], **kwargs)
        self.__itemData = args[2]
        self.__status = args[3]
        self.__statusMap = {
            TaskStatus.DECRYPTING: "Decrypting...",
            TaskStatus.DOWNLOADING_FROM_CLOUD: "Downloading from cloud!",
            TaskStatus.DOWNLOADING_FROM_REMOTE: "Downloading to local syncdir!",
            TaskStatus.ENCRYPTING: "Encrypting...",
            TaskStatus.IN_QUEUE_FOR_DOWNLOAD: "Enqueued for download!",
            TaskStatus.IN_QUEUE_FOR_UPLOAD: "Enqueued for upload!",
            TaskStatus.SYNCED: "Synced!",
            TaskStatus.UPLOADING_TO_CLOUD: "Uploading to cloud!",
            TaskStatus.UPLOADING_TO_REMOTE: "Uploading to remote!",
            TaskStatus.STATELESS: "Updating..."
        }
        self.__setup()

    def __setup(self):
        self.__layout = QtGui.QHBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(0)
        self.setFixedHeight(45)
        self.__setupItemPathLabel()
        self.__setupStatusLabel()

        self.setStyleSheet(
            """
                QWidget {
                    border:0px solid transparent;
                    border-bottom:2px solid #F2F2F2;
                }
            """
        )

        self.setLayout(self.__layout)

    def __setupItemPathLabel(self):
        itemPath = self.__itemData["path"] if self.__itemData["path"] else self.__itemData["fullPath"]
        if len(itemPath) > 39:
            self.__itemPath = QtGui.QLabel(itemPath[:37] + "...", parent=self)
            self.setToolTip(itemPath)
        else:
            self.__itemPath = QtGui.QLabel(itemPath, parent=self)
        self.__layout.addWidget(self.__itemPath)

    def __setupStatusLabel(self):
        self.__itemStatusWidget = QtGui.QLabel(self.__statusMap[self.__status])
        self.__layout.addWidget(self.__itemStatusWidget)

    def updateStatus(self, status):
        if status is not 11:
            self.__itemStatusWidget.setText(self.__statusMap[status])
            self.repaint()
