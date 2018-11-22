from PyQt4 import QtCore
import scandir
import shutil
import os

from src.model.FileTask import FileTask, TaskType


class FileManager(QtCore.QObject):

    def __init__(self, networkManager):
        super(FileManager, self).__init__()
        self.shouldRun = True
        self.networkManager = networkManager
        self.networkManager.taskReportChannel.connect(self.__taskReportHandler)
        self.fileList = []

    def start(self):
        while(self.shouldRun):
            if not self.fileList:
                self.__initFileList()
            self.shouldRun = False

    def __initFileList(self):
        settings = QtCore.QSettings()
        self.syncDir = unicode(settings.value("syncDir").toString()).encode("utf8")
        self.__pathCutLength = len(self.syncDir) + 1

        for entry in self.__scanFileTree(self.syncDir):
            self.networkManager.enqueuTask(FileTask(TaskType.EXISTENCE_CHECK, entry['dir'],entry['fullPath'], entry['filename']))

    def __taskReportHandler(self, taskReport):
        print taskReport

    def __scanFileTree(self, baseDir):
        for entry in scandir.scandir(baseDir):
            if entry.is_file():
                yield {"dir": os.path.dirname(entry.path[self.__pathCutLength:]), "fullPath": entry.path, "filename": entry.name}
            else:
                for subEntry in self.__scanFileTree(entry.path):
                    yield subEntry

    def stop(self):
        self.shouldRun = False
