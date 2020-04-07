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
    fileEvent = pyqtSignal(object)

    def __init__(self, syncDir):
        super().__init__()
        self.__syncDir = syncDir
        self.__fileStore = None
        self.__mutedFiles = []
        self.__eventQueue = Queue()

        self._detector = FileSystemEventDetector(self.__eventQueue, syncDir)
        self._logger = logger.getChild("FileSynchronizer")
        self._shouldRun = True

    def scanLocalFiles(self):
        return {data.fullPath: data for data in self.__scantree()}

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

    def __scantree(self):
        for entry in scandir(self.__syncDir):
            if entry.is_dir(follow_symlinks=False):
                yield from scantree(entry.path)
            else:
                fullPath = entry.path
                splitted = fullPath.split("/")

                path = "/".join(splitted[:-1])
                filename = splitted[-1]
                stats = entry.stat()

                yield FileData(filename=filename, modified=stats.st_mtime, size=stats.st_size, path=path, fullPath=fullPath)

    def _processEvent(self, event):
        self.fileEvent.emit(event)


class MyEventHandler(FileSystemEventHandler):

    def __init__(self, event_queue):
        super().__init__()
        self._event_queue = event_queue

    def on_any_event(self, event):
        print(event)
        # self._event_queue.put({"source": "FileDetector", "event": event})


class FileSystemEventDetector(QObject):

    def __init__(self, eventQueue, syncDir):
        super().__init__()
        self._path = syncDir
        self._eventHandler = MyEventHandler(eventQueue)
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
