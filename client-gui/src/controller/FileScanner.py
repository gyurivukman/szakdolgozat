import scandir
import os
import time
import calendar

from PyQt4 import QtCore

from src.model.FileTask import FileTask
from src.model.FileTask import FileTaskType
from ContextManager import ContextManager


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
        self.__initFileList()
        while self.shouldRun:
            self.__scanFiles()
            time.sleep(5)

    def __initFileList(self):
        pass

    def __scanFiles(self):
        currentTime = calendar.timegm(time.gmtime())
        for entry in self.__scanFileTree(self.syncDir):
            relativePath = entry['fullPath'][self.__pathCutLength:]
            if relativePath not in self.files and (currentTime - entry["lastModified"]) > 5:
                self.files[relativePath] = True
                self.__reportNewFileTask(entry)

    def __scanFileTree(self, baseDir):
        for entry in scandir.scandir(baseDir):
            if entry.is_file():
                yield {"dir": os.path.dirname(entry.path[self.__pathCutLength:]), "fullPath": entry.path, "filename": entry.name, "lastModified": entry.stat().st_mtime}
            else:
                for subEntry in self.__scanFileTree(entry.path):
                    yield subEntry

    def __reportNewFileTask(self, entry):
        self.newFileChannel.emit(FileTask(FileTaskType.EXISTENCE_CHECK, entry['dir'], entry['fullPath'], entry['filename']))

    def stop(self):
        self.shouldRun = False
