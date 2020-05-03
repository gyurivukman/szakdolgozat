import logging
import time
import os
import shutil

from uuid import uuid4
from datetime import datetime


from os import scandir
from threading import Thread
from queue import Empty
from multiprocessing import Process
from multiprocessing import Queue

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import QObject, pyqtSignal

from model.file import (
    FileEventTypes, FileData, FileStatuses,
    FileStatusEvent, CheckLaterFileEvent
)
from model.task import FileTask


logger = logging.getLogger(__name__)


def startDetector(eventQueue, syncDir):
    logger.getChild("FileSynchronizer").info("Event detector process spawned!")
    eventHandler = EnqueueAnyFileEventEventHandler(eventQueue, syncDir)
    detector = FileSystemEventDetector(eventHandler, syncDir)
    detector.start()


class FileSynchronizer(QObject):
    fileTaskChannel = pyqtSignal(FileTask)
    fileStatusChannel = pyqtSignal(FileStatusEvent)

    def __init__(self, syncDir):
        super().__init__()
        self.__syncDir = syncDir
        self.__toCheckLater = None
        self.__eventQueue = Queue()
        self.__localFilesCache = []

        self.__detectorProcess = Process(target=startDetector, args=(self.__eventQueue, self.__syncDir))
        self.__logger = logger.getChild("FileSynchronizer")
        self.__shouldRun = True

    def syncFileList(self, remoteFiles):
        self.__toCheckLater = {}

        localFiles = self.__scanLocalFiles()
        self.__localFilesCache = [*localFiles]
        mergedFileList = self.__mergeLocalFilesWithRemoteFiles(localFiles, remoteFiles)

        debug = '\n'.join([f'{key}: {value.status.name}' for key, value in mergedFileList.items()])
        self.__logger.debug(f"Merged Filelist:\n {debug}")

        for _, fileData in mergedFileList.items():
            # Created, so the UI makes a new entry
            event = FileStatusEvent(eventType=FileEventTypes.CREATED, status=fileData.status, sourcePath=fileData.fullPath)

            self.fileStatusChannel.emit(event)
            if fileData.status != FileStatuses.SYNCED:
                uuid = uuid4().hex
                task = FileTask(uuid, fileData.status, fileData)
                self.fileTaskChannel.emit(task)

    def setSyncDir(self, syncDir):
        self.__syncDir = syncDir

    def run(self):
        self.__detectorProcess.start()
        self.__logger.debug("Started detector object.")
        while self.__shouldRun:
            try:
                event = self.__eventQueue.get_nowait()
                self.__processEvent(event)
            except Empty:
                if len(self.__toCheckLater) > 0:
                    toDelete = []
                    for path, checkLaterEvent in self.__toCheckLater.items():
                        if (datetime.now() - checkLaterEvent.timeOfLastAction).seconds > 1:
                            task = self.__createTaskFromCheckLaterEvent(checkLaterEvent)
                            self.fileStatusChannel.emit(checkLaterEvent.originalEvent)
                            self.fileTaskChannel.emit(task)
                            toDelete.append(path)
                    for path in toDelete:
                        del self.__toCheckLater[path]
                else:
                    time.sleep(0.1)

        self.__logger.debug("Stopped")

    def stop(self):
        self.__shouldRun = False
        self.__logger.debug("Stopping")
        self.__detectorProcess.terminate()
        self.__detectorProcess.join()
        self.__logger.debug("Child process stopped")

    def finalizeDownload(self, task):
        self.__logger.debug("FileSyncer finalizing task.")

        absoluteSourcePath = f"{self.__syncDir}/.{task.uuid}"
        absoluteNonTriggeringPath = f"{self.__syncDir}/{task.subject.path}/.{task.uuid}" if len(task.subject.path) > 0 else absoluteSourcePath
        absoluteTargetPath = f"{self.__syncDir}/{task.subject.fullPath}"

        try:
            os.utime(absoluteSourcePath, (task.subject.modified, task.subject.modified))
            shutil.move(absoluteSourcePath, absoluteNonTriggeringPath)
            time.sleep(0.5)
            shutil.move(absoluteNonTriggeringPath, absoluteTargetPath)
        except FileNotFoundError:
            directories = task.subject.fullPath.split("/")[:-1]
            targetDirPath = f"{self.__syncDir}"
            for dirName in directories:
                targetDirPath = f"{targetDirPath}/{dirName}"
                try:
                    os.mkdir(targetDirPath)
                except FileExistsError:
                    pass
            shutil.move(absoluteSourcePath, absoluteNonTriggeringPath)
            time.sleep(0.5)
            shutil.move(absoluteNonTriggeringPath, absoluteTargetPath)

        if task.subject.fullPath not in self.__localFilesCache:
            self.__localFilesCache.append(task.subject.fullPath)

        event = FileStatusEvent(eventType=FileEventTypes.STATUS_CHANGED, sourcePath=task.subject.fullPath, status=FileStatuses.SYNCED)
        self.__logger.debug(f"Emitting event {event}")
        self.fileStatusChannel.emit(event)

    def __mergeLocalFilesWithRemoteFiles(self, localFiles, remoteFiles):
        mergedFiles = localFiles
        for remoteFile in remoteFiles:
            if remoteFile.fullPath not in mergedFiles:
                # Only Exists On Remote
                remoteFile.status = FileStatuses.DOWNLOADING_FROM_CLOUD
                mergedFiles[remoteFile.fullPath] = remoteFile
            else:
                # Exists on both.
                if remoteFile.modified > mergedFiles[remoteFile.fullPath].modified:
                    # Remote is newer.
                    mergedFiles[remoteFile.fullPath].modified = remoteFile.modified
                    mergedFiles[remoteFile.fullPath].status = FileStatuses.DOWNLOADING_FROM_CLOUD
                elif remoteFile.modified < mergedFiles[remoteFile.fullPath].modified:
                    # Local is newer.
                    mergedFiles[remoteFile.fullPath].status = FileStatuses.UPLOADING_FROM_LOCAL
                else:
                    # Synced
                    mergedFiles[remoteFile.fullPath].status = FileStatuses.SYNCED
        return mergedFiles

    def __scanLocalFiles(self):
        return {data.fullPath: data for data in self.__scantree(self.__syncDir)}

    def __scantree(self, path):
        for entry in scandir(path):
            if entry.is_dir(follow_symlinks=False):
                yield from self.__scantree(entry.path)
            else:
                fullPath = entry.path.replace(f"{self.__syncDir}/", "")
                splitted = fullPath.split("/")
                filename = splitted[-1]
                if not filename.startswith("."):
                    path = "/".join(splitted[:-1])
                    stats = entry.stat()
                    yield FileData(filename=filename, modified=int(stats.st_mtime), size=stats.st_size, path=path, fullPath=fullPath, status=FileStatuses.UPLOADING_FROM_LOCAL)
                else:
                    os.unlink(entry.path)

    def __processEvent(self, event):
        eventType = FileEventTypes(event.event_type)
        sourcePath = event.src_path.replace(f"{self.__syncDir}/", "")

        if eventType == FileEventTypes.DELETED:
            # User could've changed his mind about a file being uploaded that was modified/created before.
            try:
                del self.__toCheckLater[sourcePath]
            except KeyError:
                pass
            self.__localFilesCache.remove(sourcePath)
            event = FileStatusEvent(eventType=eventType, status=None, sourcePath=sourcePath, destinationPath=None)
            task = FileTask(uuid4().hex, FileStatuses.DELETED, subject=sourcePath)
            self.fileStatusChannel.emit(event)
            self.fileTaskChannel.emit(task)
        elif eventType == FileEventTypes.CREATED:
            if sourcePath not in self.__localFilesCache:
                self.__localFilesCache.append(sourcePath)
                self.__checkFileLater(sourcePath, eventType)
            else:
                event = FileStatusEvent(eventType=FileEventTypes.STATUS_CHANGED, sourcePath=sourcePath, status=FileStatuses.UPLOADING_FROM_LOCAL)
                fileData = self.__createFileDataFromPath(sourcePath)
                fileData.status = FileStatuses.UPLOADING_FROM_LOCAL
                task = FileTask(uuid4().hex, FileStatuses.UPLOADING_FROM_LOCAL, subject=fileData)

                self.fileStatusChannel.emit(event)
                self.fileTaskChannel.emit(task)
        elif eventType == FileEventTypes.MODIFIED:
            self.__checkFileLater(sourcePath, eventType)
        elif eventType == FileEventTypes.MOVED:
            destinationPath = event.dest_path.replace(f"{self.__syncDir}/", "")
            fileData = self.__createFileDataFromPath(destinationPath)

            self.__localFilesCache.remove(sourcePath)
            self.__localFilesCache.append(destinationPath)

            event = FileStatusEvent(eventType=FileEventTypes.STATUS_CHANGED, sourcePath=sourcePath, status=FileStatuses.MOVING)
            subject = {"sourcePath": sourcePath, "target": fileData, "moveResultCallBack": self.__onMoveFileResponse}
            task = FileTask(uuid=uuid4().hex, taskType=FileStatuses.MOVING, subject=subject)

            self.fileStatusChannel.emit(event)
            self.fileTaskChannel.emit(task)

    def __checkFileLater(self, sourcePath, eventType):
        try:
            # A file is still being copied or moved over into the syncdir.
            self.__toCheckLater[sourcePath].timeOfLastAction = datetime.now()
        except KeyError:
            # A file is being created/being modified, caught for the first time
            originalEvent = FileStatusEvent(eventType=eventType, status=FileStatuses.UPLOADING_FROM_LOCAL, sourcePath=sourcePath)
            checkLaterEvent = CheckLaterFileEvent(originalEvent, datetime.now())
            self.__toCheckLater[sourcePath] = checkLaterEvent

    def __createFileDataFromPath(self, sourcePath):
        stats = os.stat(f"{self.__syncDir}/{sourcePath}")
        splitted = sourcePath.split("/")

        filename = splitted[-1]
        modified = int(stats.st_mtime)
        size = stats.st_size
        path = "/".join(splitted[:-1])
        fullPath = sourcePath

        return FileData(filename, modified, size, path, fullPath)

    def __createTaskFromCheckLaterEvent(self, checkLaterEvent):
        fileData = self.__createFileDataFromPath(checkLaterEvent.originalEvent.sourcePath)
        fileData.status = checkLaterEvent.originalEvent.status
        task = FileTask(uuid=uuid4().hex, taskType=FileStatuses.UPLOADING_FROM_LOCAL, subject=fileData)

        return task

    def __onMoveFileResponse(self, data):
        if data["moveSuccessful"]:
            self.__logger.debug(f"Moving from {data['from']} to {data['to']} successful, updating local data.")
            event = FileStatusEvent(eventType=FileEventTypes.MOVED, sourcePath=data["from"], destinationPath=data["to"], status=FileStatuses.SYNCED)
            self.fileStatusChannel.emit(event)
        else:
            self.__logger.debug(f"Moving from {data['from']} to {data['to']} was unsuccessful, reuploading file again.")
            fileData = self.__createFileDataFromPath(data["to"])
            event = FileStatusEvent(eventType=FileEventTypes.MOVED, sourcePath=data["from"], destinationPath=data["to"], status=FileStatuses.UPLOADING_FROM_LOCAL)
            task = FileTask(uuid=uuid4().hex, taskType=FileStatuses.UPLOADING_FROM_LOCAL, subject=fileData)

            self.fileStatusChannel.emit(event)
            self.fileTaskChannel.emit(task)


class EnqueueAnyFileEventEventHandler(FileSystemEventHandler):

    def __init__(self, eventQueue, syncDir):
        super().__init__()
        self.__eventQueue = eventQueue
        self.__syncDirStartIndex = len(syncDir)

    def on_any_event(self, event):
        if self.__canReportEvent(event):
            self.__eventQueue.put(event)

    def __canReportEvent(self, event):
        return not event.is_directory and not self.__isHiddenFileEvent(event.src_path)

    def __isHiddenFileEvent(self, srcPath):
        return srcPath.split("/")[-1][0] == "."


class FileSystemEventDetector(QObject):

    def __init__(self, eventHandler, pathToWatch):
        super().__init__()
        self.__eventHandler = eventHandler
        self.__path = pathToWatch
        self.__observer = Observer()
        self.__logger = logger.getChild("FileSystemEventDetector")

    def start(self):
        self.__logger.info("Starting file detector")
        self.__observer.schedule(self.__eventHandler, self.__path, recursive=True)
        self.__observer.start()
        while True:
            time.sleep(0.02)
