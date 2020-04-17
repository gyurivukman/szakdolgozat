import logging
import time
import os

from uuid import uuid4
from datetime import datetime


from os import scandir
from threading import Thread
from queue import Empty, Queue

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import QObject, pyqtSignal

from model.file import (
    FileEventTypes, FileData, FileStatuses,
    FileStatusEvent, CheckLaterFileEvent
)
from model.task import FileTask


logger = logging.getLogger(__name__)


class FileSynchronizer(QObject):
    fileTaskChannel = pyqtSignal(FileTask)
    fileStatusChannel = pyqtSignal(FileStatusEvent)

    def __init__(self, syncDir):
        super().__init__()
        self.__syncDir = syncDir
        self.__toCheckLater = None
        self.__eventQueue = Queue()

        self.__detector = FileSystemEventDetector(self.__eventQueue, syncDir)
        self.__logger = logger.getChild("FileSynchronizer")
        self.__shouldRun = True

    def syncFileList(self, remoteFiles):
        self.__toCheckLater = {}

        localFiles = self.__scanLocalFiles()
        mergedFileList = self.__mergeLocalFilesWithRemoteFiles(localFiles, remoteFiles)

        debug = '\n'.join([f'{key}: {value.status.name}' for key, value in mergedFileList.items()])
        self.__logger.debug(f"Merged Filelist:\n {debug}")

        for _, fileData in mergedFileList.items():
            # Created, so the UI makes a new entry
            event = FileStatusEvent(eventType=FileEventTypes.CREATED, status=fileData.status, sourcePath=fileData.fullPath)

            self.fileStatusChannel.emit(event)
            if fileData.status != FileStatuses.SYNCED:
                uuid = uuid4().hex
                if fileData.status == FileStatuses.DOWNLOADING_FROM_CLOUD:
                    self.__detector.muteFile(f"{self.__syncDir}/.{uuid}")
                task = FileTask(uuid, fileData.status, fileData)
                self.fileTaskChannel.emit(task)

    def setSyncDir(self, syncDir):
        self.__syncDir = syncDir

    def run(self):
        self.__detector.start()
        self.__logger.debug("Started detector object.")
        while self.__shouldRun:
            try:
                event = self.__eventQueue.get_nowait()
                self.__processEvent(event)
                self.__eventQueue.task_done()
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
                    time.sleep(0.02)
        self.__logger.debug("Stopped")

    def stop(self):
        self.__shouldRun = False
        self.__logger.debug("Stopping")
        self.__detector.stop()

    def finalizeDownload(self, task):
        self.__logger.debug("FileSyncer finalizing task.")

        absoluteSourcePath = f"{self.__syncDir}/.{task.uuid}"
        absoluteTargetPath = f"{self.__syncDir}/{task.subject.fullPath}"

        self.__detector.muteFile(absoluteTargetPath)
        time.sleep(0.2)
        try:
            os.rename(absoluteSourcePath, absoluteTargetPath)
        except FileNotFoundError:
            splitted = task.subject.fullPath.split("/")[:-1]
            targetDirPath = f"{self.__syncDir}"
            for dirName in splitted:
                targetDirPath = f"{targetDirPath}/{dirName}"
                os.mkdir(targetDirPath)
            os.rename(absoluteSourcePath, absoluteTargetPath)

        os.utime(absoluteTargetPath, (task.subject.modified, task.subject.modified))

        event = FileStatusEvent(eventType=FileEventTypes.STATUS_CHANGED, sourcePath=task.subject.fullPath, status=FileStatuses.SYNCED)
        self.__logger.debug(f"Emitting event {event}")
        self.fileStatusChannel.emit(event)

        self.__detector.unMuteFile(absoluteSourcePath)
        self.__detector.unMuteFile(absoluteTargetPath)

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

                path = "/".join(splitted[:-1])
                filename = splitted[-1]
                stats = entry.stat()

                yield FileData(filename=filename, modified=int(stats.st_mtime), size=stats.st_size, path=path, fullPath=fullPath, status=FileStatuses.UPLOADING_FROM_LOCAL)

    def __processEvent(self, event):
        eventType = FileEventTypes(event.event_type)
        sourcePath = event.src_path.replace(f"{self.__syncDir}/", "")
        destinationPath = getattr(event, "dest_path", None)
        destinationPath = destinationPath.replace(f"{self.__syncDir}/", "") if destinationPath else None
        if eventType == FileEventTypes.DELETED:
            # User could've changed his mind about a file being uploaded that was modified/created before.
            try:
                del self.__toCheckLater[sourcePath]
            except Keyerror:
                pass
            event = FileStatusEvent(eventType=eventType, status=FileStatuses.MOVING, sourcePath=sourcePath, destinationPath=destinationPath)
            self.fileStatusChannel.emit(event)
            # TODO hogy akkor még konkrét task is legyen belőle.
        elif eventType == FileEventTypes.CREATED or eventType == FileEventTypes.MODIFIED:
            try:
                # A file is still being copied or moved over into the syncdir.
                self.__toCheckLater[sourcePath].timeOfLastAction = datetime.now()
            except KeyError:
                # A file is being created/being modified, caught for the first time
                originalEvent = FileStatusEvent(eventType=eventType, status=FileStatuses.UPLOADING_FROM_LOCAL, sourcePath=sourcePath)
                checkLaterEvent = CheckLaterFileEvent(originalEvent, datetime.now())
                self.__toCheckLater[sourcePath] = checkLaterEvent

    def __createTaskFromCheckLaterEvent(self, checkLaterEvent):
        stats = os.stat(f"{self.__syncDir}/{checkLaterEvent.originalEvent.sourcePath}")
        splitted = checkLaterEvent.originalEvent.sourcePath.split("/")

        filename = splitted[-1]
        modified = int(stats.st_mtime)
        size = stats.st_size
        path = "/".join(splitted[:-1])
        fullPath = checkLaterEvent.originalEvent.sourcePath

        fileData = FileData(filename, modified, size, path, fullPath, checkLaterEvent.originalEvent.status)
        task = FileTask(uuid4().hex, FileStatuses.UPLOADING_FROM_LOCAL, fileData)

        return task


class EnqueueAnyFileEventEventHandler(FileSystemEventHandler):

    def __init__(self, eventQueue):
        super().__init__()
        self.__eventQueue = eventQueue
        self.__mutedFiles = set()

    def on_any_event(self, event):
        if not event.is_directory:
            if event.src_path not in self.__mutedFiles:
                self.__eventQueue.put(event)

    def muteFile(self, path):
        self.__mutedFiles.add(path)

    def unMuteFile(self, path):
        self.__mutedFiles.remove(path)


class FileSystemEventDetector(QObject):

    def __init__(self, eventQueue, syncDir):
        super().__init__()
        self._path = syncDir
        self._eventHandler = EnqueueAnyFileEventEventHandler(eventQueue)
        self._observer = Observer()
        self._logger = logger.getChild("FileSystemEventDetector")

    def start(self):
        self._logger.debug("Starting file detector")
        self._observer.schedule(self._eventHandler, self._path, recursive=True)
        self._observer.start()

    def stop(self):
        self._logger.debug("Stopping observer")
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
            self._logger.debug("Stopped observer")
        self._logger.debug("Stopped detector.")

    def muteFile(self, path):
        self._eventHandler.muteFile(path)

    def unMuteFile(self, path):
        self._eventHandler.unMuteFile(path)
