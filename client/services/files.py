import time
import logging


from os import scandir
from threading import Thread
from queue import Empty, Queue

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import QObject, pyqtSignal

from model.file import FileTask, FileEventTypes, FileData, FileStatuses, FileStatusEvent, FileStatusEventData


logger = logging.getLogger(__name__)


class FileSynchronizer(QObject):
    fileTaskChannel = pyqtSignal(FileTask)
    fileStatusChannel = pyqtSignal(FileStatusEvent)

    def __init__(self, syncDir):
        super().__init__()
        self.__syncDir = syncDir
        self.__toCheckLater = None
        self.__mutedFiles = None
        self.__eventQueue = Queue()

        self.__detector = FileSystemEventDetector(self.__eventQueue, syncDir)
        self.__logger = logger.getChild("FileSynchronizer")
        self.__shouldRun = True

    def syncFileList(self, remoteFiles):
        self.__mutedFiles = []
        self.__toCheckLater = {}

        localFiles = self.__scanLocalFiles()
        mergedFileList = self.__mergeLocalFilesWithRemoteFiles(localFiles, remoteFiles)

        debug = '\n'.join([f'{key}: {value.status.name}' for key, value in mergedFileList.items()])
        self.__logger.debug(f"Merged Filelist:\n {debug}")

        for _, fileData in mergedFileList.items():

            eventData = FileStatusEventData(fileData.filename, fileData.path, fileData.fullPath)
            event = FileStatusEvent(eventType=FileEventTypes.CREATED, status=fileData.status, source=eventData, destination=None)

            self.fileStatusChannel.emit(event)
            if fileData.status != FileStatuses.SYNCED:
                # TODO hogy akkor még konkrét task is legyen belőle.
                pass

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

    def setSyncDir(self, syncDir):
        self.__syncDir = syncDir

    def run(self):
        self.__detector.start()
        self.__logger.debug("Started detector object.")
        while self.__shouldRun:
            try:
                event = self.__eventQueue.get_nowait()
                self._processEvent(event)
                self.__eventQueue.task_done()
            except Empty as _:
                time.sleep(0.5)
        self.__logger.debug("Stopped")

    def stop(self):
        self.__shouldRun = False
        self.__logger.debug("Stopping")
        self.__detector.stop()

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

                yield FileData(filename=filename, modified=stats.st_mtime, size=stats.st_size, path=path, fullPath=fullPath, status=FileStatuses.UPLOADING_FROM_LOCAL)

    def _processEvent(self, event):
        eventType = FileEventTypes(event.event_type)
        if eventType == FileEventTypes.DELETED:
            fullPath = event.src_path.replace(f"{self.__syncDir}/", "")
            task = FileTask(FileEventTypes.DELETED, fullPath)
            # self.fileStatusChannel.emit(task)


class EnqueueAnyFileEventEventHandler(FileSystemEventHandler):

    def __init__(self, eventQueue):
        super().__init__()
        self.__eventQueue = eventQueue

    def on_any_event(self, event):
        if not event.is_directory:
            self.__eventQueue.put(event)


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
