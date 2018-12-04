import scandir
import os
import time
import calendar

from PyQt4 import QtCore
from src.model.Task import Task, TaskTypes
from src.model.FileDescription import FileDescription


class FileScanner(QtCore.QObject):
    newFileChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FileScanner, self).__init__()
        self.__setup()

    def __setup(self):
        self.__settings = QtCore.QSettings()
        self.__shouldRun = True
        self.__canExecute = True
        self.__files = {}
        self.setSyncDir(unicode(self.__settings.value('syncDir').toString()).encode("utf8"))

    def setSyncDir(self, syncDir):
        self.__syncdir = syncDir
        self.__pathCutLength = len(self.__syncdir)

    def syncInitialFileList(self, fileList):
        self.__files = {}
        time.sleep(2)
        print "filescanner initial filelist SET!"
        return []

    def start(self):
        while self.__shouldRun:
            if self.__canExecute:
                self.__scanFiles()
            time.sleep(5)

    def pause(self):
        self.__canExecute = False

    def resume(self):
        self.__canExecute = True

    def isPaused(self):
        return not self.__canExecute

    def __scanFiles(self):
        currentTime = calendar.timegm(time.gmtime())
        for entry in self.__scanFileTree(self.__syncdir):
            relativePath = entry['fullPath'][self.__pathCutLength:]
            if relativePath not in self.__files and (currentTime - entry["lastModified"]) > 5:
                self.__files[relativePath] = True
                self.__reportNewFileTask(entry)

    def __scanFileTree(self, baseDir):
        for entry in scandir.scandir(baseDir):
            if entry.is_file():
                stats = entry.stat()
                yield {
                        "dir": os.path.dirname(entry.path[self.__pathCutLength:]),
                        "fullPath": entry.path,
                        "filename": entry.name, 
                        "lastModified": stats.st_mtime,
                        "size": stats.st_size
                    }
            else:
                for subEntry in self.__scanFileTree(entry.path):
                    yield subEntry

    def __reportNewFileTask(self, entry):
        fileDesc = FileDescription(targetDir=entry["dir"], fullPath=entry["fullPath"], fileName=entry["filename"], lastModified=entry["lastModified"], size=entry["size"])
        self.newFileChannel.emit(Task(taskType=TaskTypes.EXISTENCE_CHECK, subject=fileDesc))

    def stop(self):
        self.__shouldRun = False
