import scandir
import os
import time

from PyQt4 import QtCore

from src.model.FileTask import FileTask
from src.model.FileTask import FileTaskType


class FileScanner(QtCore.QObject):
    newFileChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FileScanner, self).__init__()
        self.__setup()

    def __setup(self):
        self.settings = QtCore.QSettings()
        self.shouldRun = True
        self.files = {}
        self.setSyncDir(unicode(self.settings.value('syncDir').toString()).encode("utf8"))

    def setSyncDir(self, syncDir):
        self.syncDir = syncDir
        self.__pathCutLength = len(self.syncDir)

    def start(self):
        while self.shouldRun:
            self.__scanFiles()
            time.sleep(4)

    def __scanFiles(self):
        for entry in self.__scanFileTree(self.syncDir):
            relativePath = entry['fullPath'][self.__pathCutLength:]
            if relativePath not in self.files:
                print "[INFO] Filescanner: New file found: {}".format(relativePath)
                self.files[relativePath] = True
                self.newFileChannel.emit(FileTask(FileTaskType.EXISTENCE_CHECK, entry['dir'], entry['fullPath'], entry['filename']))

    def __scanFileTree(self, baseDir):
        for entry in scandir.scandir(baseDir):
            if entry.is_file():
                yield {"dir": os.path.dirname(entry.path[self.__pathCutLength:]), "fullPath": entry.path, "filename": entry.name}
            else:
                for subEntry in self.__scanFileTree(entry.path):
                    yield subEntry

    def stop(self):
        self.shouldRun = False
