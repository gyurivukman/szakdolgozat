import scandir
import os
import time
import calendar

from PyQt4 import QtCore
from watchdog.observers import Observer

from src.controller.FileEventBroker import FileEventBroker

from src.model.Task import Task, TaskTypes
from src.model.FileDescription import FileDescription


class FileScanner(QtCore.QObject):
    fileStatusChangeChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FileScanner, self).__init__()
        self.__setup()

    def __setup(self):
        self.__settings = QtCore.QSettings()
        self.__shouldRun = True
        self.__newFilesInWriting = {}
        self.setSyncDir(unicode(self.__settings.value('syncDir').toString()).encode("utf8"))
        self.__pathCutLength = len(self.__syncdir)

        self.__event_handler = FileEventBroker()
        self.__event_handler.fileEventChannel.connect(self.__handleFileChangeEvent)
        self.__observer = Observer()
        self.__observer.schedule(self.__event_handler, self.__syncdir, recursive=True)

    def setSyncDir(self, syncDir):
        self.__syncdir = syncDir

    def syncInitialFileList(self, fileList):
        self.__filesCache = {}
        for remoteFile in fileList:
            self.__filesCache[remoteFile["path"]] = remoteFile
        self.__scanLocalFiles()
        return self.__filesCache

    def start(self):
        print "Filescanner starting observer"
        self.__observer.start()
        print "Observer started!"
        while self.__shouldRun:
            time.sleep(5)
            if self.__checkFilesInWriting:
                self.__checkFilesInWriting()

    def __scanLocalFiles(self):
        currentTime = calendar.timegm(time.gmtime())
        localFiles = {localFile['fullPath'][self.__pathCutLength:]: localFile for localFile in self.__scanFileTree(self.__syncdir)}

        for relativePath, localFile in localFiles.iteritems():
            if relativePath not in self.__filesCache:
                if (currentTime - localFile["lastModified"]) > 5:
                    print "localfile stable and does not exist, uploading.." + str(localFile)
                    self.__filesCache[relativePath] = localFile
                    self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.UPLOAD, subject=localFile))
                elif (currentTime - localFile["lastModified"]) < 5 and localFile[relativePath] not in self.__newFilesInWriting:
                    print "localfile unstable and does not exist, delaying for upload " + str(localFile)
                    self.__newFilesInWriting[relativePath] = localFile
            else:
                if localFile["lastModified"] > self.__filesCache[relativePath]["lastModified"]:
                    if (currentTime - localFile["lastModified"]) > 5:
                        print "local file is newer and stable, uploading..." + str(localFile)
                        self.__filesCache[relativePath] = localFile
                        self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.UPLOAD, subject=localFile))
                    else:
                        print "local file is newer, but unstable, delaying for upload" + str(localFile)
                        self.__newFilesInWriting[relativePath] = localFile
                else:
                    print "local file is older, downloading remote " + str(localFile)
                    self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.DOWNLOAD, subject=self.__filesCache[relativePath]))

        # Syncing files that dont exist locally
        for relativePath, cachedFile in self.__filesCache.iteritems():
            if relativePath not in localFiles:
                print "remotefile not in localfiles, uploading" + str(cachedFile)
                self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.DOWNLOAD, subject=cachedFile))

    def __scanFileTree(self, baseDir):
        for localFile in scandir.scandir(baseDir):
            if localFile.is_file():
                stats = localFile.stat()
                yield {
                        "dir": os.path.dirname(localFile.path[self.__pathCutLength:]).lstrip('/'),
                        "fullPath": localFile.path.lstrip('/'),
                        "filename": localFile.name, 
                        "lastModified": stats.st_mtime,
                        "size": stats.st_size
                    }
            else:
                for subLocalFile in self.__scanFileTree(localFile.path):
                    yield subLocalFile

    def __checkFilesInWriting(self):
        currentTime = calendar.timegm(time.gmtime())
        for relativePath in self.__newFilesInWriting.keys():
            stats = os.stat(self.__newFilesInWriting[relativePath]["fullPath"])
            if currentTime - stats.st_mtime > 5000:
                print "Found a finished file!" + str(self.__newFilesInWriting[relativePath])
                self.__filesCache[relativePath] = self.__newFilesInWriting[relativePath]
                self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.DOWNLOAD, subject=self.__newFilesInWriting[relativePath]))
                del self.__newFilesInWriting[relativePath]

    def __handleFileChangeEvent(self, event):
        print "fileChangeEvent in filescanner " + str(event)

    def stop(self):
        self.__shouldRun = False
        self.__observer.stop()
        self.__observer.join()
