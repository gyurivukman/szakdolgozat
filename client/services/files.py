import time
import logging


from os import scandir
from threading import Thread
from queue import Empty, Queue

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import QObject, pyqtSignal

from model.file import FileData


logger = logging.getLogger(__name__)


class FileSynchronizer(QObject):
    fileTaskChannel = pyqtSignal(object)
    fileStatusChannel = pyqtSignal(object)

    def __init__(self, syncDir):
        super().__init__()
        self.__syncDir = syncDir
        self.__toCheckLater = None
        self.__mutedFiles = None
        self.__eventQueue = Queue()

        self._detector = FileSystemEventDetector(self.__eventQueue, syncDir)
        self._logger = logger.getChild("FileSynchronizer")
        self._shouldRun = True

    def syncFileList(self, remoteFiles):
        self.__mutedFiles = []
        self.__toCheckLater = {}

        localFiles = self.__scanLocalFiles()

        self._logger.debug(f"\n\nMerging local files\n{localFiles}\nwith remote files\n{remoteFiles}")

    def __scanLocalFiles(self):
        return {data.fullPath: data for data in self.__scantree(self.__syncDir)}

    def setSyncDir(self, syncDir):
        self.__syncDir = syncDir

    def run(self):
        self._detector.start()
        self._logger.debug("Started detector object.")
        while self._shouldRun:
            try:
                event = self.__eventQueue.get_nowait()
                self._processEvent(event)
                self.__eventQueue.task_done()
            except Empty as _:
                time.sleep(0.5)
        self._logger.debug("Stopped")

    def stop(self):
        self._shouldRun = False
        self._logger.debug("Stopping")
        self._detector.stop()

    def __scantree(self, path):
        for entry in scandir(path):
            if entry.is_dir(follow_symlinks=False):
                yield from self.__scantree(entry.path)
            else:
                fullPath = entry.path
                splitted = fullPath.split("/")

                path = "/".join(splitted[:-1])
                filename = splitted[-1]
                stats = entry.stat()

                yield FileData(filename=filename, modified=stats.st_mtime, size=stats.st_size, path=path, fullPath=fullPath)

    def _processEvent(self, event):
        self.fileTaskChannel.emit(event)


class EnqueueAnyFileEventEventHandler(FileSystemEventHandler):

    def __init__(self, eventQueue):
        super().__init__()
        self.__eventQueue = eventQueue

    def on_any_event(self, event):
        if not event.is_dir:
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
