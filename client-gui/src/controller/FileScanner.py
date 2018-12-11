import scandir
import os
import time
import datetime
from threading import RLock

from PyQt4 import QtCore
from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent
from src.controller.FileEventBroker import FileEventBroker

from src.model.Task import Task, TaskTypes
import src.model.TaskStatus as TaskStatus
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
        self.__lock = RLock()
        self.setSyncDir(unicode(self.__settings.value('syncDir').toString()).encode("utf8"))
        self.__pathCutLength = len(self.__syncdir) + 1

        self.__event_handler = FileEventBroker()
        self.__event_handler.fileEventChannel.connect(self.__handleFileChangeEvent)
        self.__observer = Observer()
        self.__observer.schedule(self.__event_handler, self.__syncdir, recursive=True)

    def setSyncDir(self, syncDir):
        self.__syncdir = syncDir

    def syncInitialFileList(self, fileList):
        self.__filesCache = {}
        for remoteFile in fileList:
            remoteFile["fullPath"] = self.__syncdir+'/'+remoteFile["path"]
            self.__filesCache[remoteFile["path"]] = remoteFile
        self.__scanLocalFiles()

    def start(self):
        self.__observer.start()
        while self.__shouldRun:
            if self.__checkFilesInWriting:
                self.__checkFilesInWriting()
            time.sleep(3)

    def __scanLocalFiles(self):
        currentTime = int(time.time())
        localFiles = {localFile['path']: localFile for localFile in self.__scanFileTree(self.__syncdir)}

        for relativePath, localFile in localFiles.iteritems():
            if relativePath not in self.__filesCache:
                if currentTime - localFile["lastModified"] > 5:
                    print "localfile stable and does not exist, uploading: {}".format(localFile["fullPath"])
                    self.__filesCache[relativePath] = localFile
                    self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.UPLOAD, subject=localFile, status=TaskStatus.IN_QUEUE_FOR_UPLOAD))
                elif (currentTime - localFile["lastModified"]) < 5 and localFile[relativePath] not in self.__newFilesInWriting:
                    print "localfile unstable and does not exist, delaying for upload: {}".format(localFile["fullPath"])
                    self.__newFilesInWriting[relativePath] = localFile
            else:
                if localFile["lastModified"] > self.__filesCache[relativePath]["lastModified"] and currentTime - localFile["lastModified"] > 5:
                    if currentTime > localFile["lastModified"]:
                        print "local file is newer and stable, uploading: {}".format(localFile["fullPath"])
                        localFile["lastModified"] = self.__filesCache[relativePath]["lastModified"]
                        self.__filesCache[relativePath] = localFile
                        self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.UPLOAD, subject=localFile, status=TaskStatus.IN_QUEUE_FOR_UPLOAD))
                    else:
                        print "local file is newer, but unstable, delaying for upload: {}".format(localFile["fullPath"])
                        self.__newFilesInWriting[relativePath] = localFile
                elif localFile["lastModified"] < self.__filesCache[relativePath]["lastModified"]:
                    print "rlocalfile is older, downloading remote " + str(localFile)
                    self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.DOWNLOAD, subject=self.__filesCache[relativePath], status=TaskStatus.IN_QUEUE_FOR_DOWNLOAD))
                else:
                    print "Local file is in sync!"
                    self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.IGNORE, subject=self.__filesCache[relativePath], status=TaskStatus.SYNCED))

        # Syncing files that dont exist locally
        for relativePath, cachedFile in self.__filesCache.iteritems():
            if relativePath not in localFiles:
                cachedFile["fullPath"] = self.__syncdir + '/' + cachedFile["path"]
                print "remotefile not in localfiles, downlading: {}".format(cachedFile["fullPath"])
                self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.DOWNLOAD, subject=cachedFile, status=TaskStatus.IN_QUEUE_FOR_DOWNLOAD))

    def __scanFileTree(self, baseDir):
        for localFile in scandir.scandir(baseDir):
            if localFile.is_file():
                stats = localFile.stat()
                yield {
                        "fullPath": localFile.path,
                        "path": localFile.path[self.__pathCutLength:],
                        "fileName": localFile.name,
                        "lastModified": int(stats.st_mtime),
                        "size": stats.st_size
                    }
            else:
                for subLocalFile in self.__scanFileTree(localFile.path):
                    yield subLocalFile

    def __checkFilesInWriting(self):
        self.__lock.acquire()
        currentTime = int(time.time())
        for relativePath in self.__newFilesInWriting.keys():
            newFile = self.__newFilesInWriting[relativePath]
            stats = os.stat(newFile["fullPath"])
            if currentTime - stats.st_mtime > 5:
                print "Found a finished file: {}".format(newFile["fullPath"])
                newFile["lastModified"] = stats.st_mtime
                self.__filesCache[relativePath] = newFile
                self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.UPLOAD, subject=self.__newFilesInWriting[relativePath], status=TaskStatus.IN_QUEUE_FOR_UPLOAD))
                del self.__newFilesInWriting[relativePath]
            else:
                print "File still being modified, delaying upload again!"
        self.__lock.release()

    def __handleFileChangeEvent(self, event):
        self.__lock.acquire()
        print event
        if self.__shouldTrack(event):
            self.__handleTrackEvent(event)
        elif self.__isDeletionEvent(event):
            self.__handleDeletionEvent(event)
        self.__lock.release()

    def __shouldTrack(self, event):
        return isinstance(event, FileCreatedEvent) or isinstance(event, FileModifiedEvent)

    def __handleTrackEvent(self, event):
        fullPath = event.src_path
        relativePath = fullPath[self.__pathCutLength:]
        if relativePath not in self.__filesCache:
            stats = os.stat(fullPath)
            newFile = {
                "fullPath": fullPath,
                "path": relativePath,
                "fileName": fullPath.split('/')[-1],
                "lastModified": int(stats.st_mtime),
                "size": stats.st_size
            }
            self.__newFilesInWriting[relativePath] = newFile

    def __isDeletionEvent(self, event):
        return isinstance(event, FileDeletedEvent)

    def __handleDeletionEvent(self, event):
        relativePath = event.src_path[self.__pathCutLength:]
        data = self.__filesCache[relativePath]
        self.fileStatusChangeChannel.emit(Task(taskType=TaskTypes.DELETEFILE, subject=data, status=TaskStatus.STATELESS))
        del self.__filesCache[relativePath]

    def stop(self):
        self.__shouldRun = False
        self.__observer.stop()
        self.__observer.join()
