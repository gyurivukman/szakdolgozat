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
    
    def __init__(self):
        super().__init__()
        self._eventQueue = Queue()
        self._detector = FileSystemEventDetector(self._eventQueue)
        self._detectorThread = Thread(target=self._detector.run)
        self._logger = logger.getChild("FileSynchronizer")
        self._shouldRun = True

    def run(self):
        self._detectorThread.start()
        while self._shouldRun:
            try:
                event = self._eventQueue.get_nowait()
                self._processEvent(event)
            except Empty as _:
                time.sleep(1)
        self._logger.debug("Stopped")

    def stop(self):
        self._shouldRun = False
        self._logger.debug("Stopping")
        self._detector.stop()
        self._detectorThread.join()

    def _processEvent(self, event):
        self.fileEvent.emit(event)


class MyEventHandler(FileSystemEventHandler):

    def __init__(self, event_queue):
        super().__init__()
        self._event_queue = event_queue

    def on_any_event(self, event):
        self._event_queue.put({"source": "FileDetector", "event":event})


class FileSystemEventDetector(QObject):

    def __init__(self,event_queue):
        super().__init__()
        self._path = "/home/gyuri/Asztal/sync_dir"
        self._event_handler = MyEventHandler(event_queue)
        self._observer = Observer()
        self._logger = logger.getChild("FileSystemEventDetector")
        self._shouldRun = True
    
    def run(self):
        self._logger.debug("Starting file detector")
        self._observer.schedule(self._event_handler, self._path, recursive=True)
        self._observer.start()

        while self._shouldRun:
            time.sleep(1)
        self._logger.debug("Stopping observer")
        self._observer.stop()
        self._logger.debug("Stopped observer")
        self._observer.join()
        self._logger.debug("Stopped detector.")

    def stop(self):
        self._logger.debug("Stopping")
        self._shouldRun = False