import time
import logging

from threading import Thread
from queue import Empty, Queue

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from PyQt5.QtCore import QObject, pyqtSignal


logger = logging.getLogger(__name__)


class FileSynchronizer(QObject):
    fileEvent = pyqtSignal(object)

    def __init__(self, syncDir):
        super().__init__()
        self._eventQueue = Queue()
        self._detector = FileSystemEventDetector(self._eventQueue, syncDir)
        self._logger = logger.getChild("FileSynchronizer")
        self._shouldRun = True

    def run(self):
        self._detector.start()
        self._logger.debug("Started detector object.")
        while self._shouldRun:
            try:
                event = self._eventQueue.get_nowait()
                self._processEvent(event)
                self._eventQueue.task_done()
            except Empty as _:
                time.sleep(0.5)
        self._logger.debug("Stopped")

    def stop(self):
        self._shouldRun = False
        self._logger.debug("Stopping")
        self._detector.stop()

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
