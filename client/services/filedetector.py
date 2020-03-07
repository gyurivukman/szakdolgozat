import time
import logging

from queue import Empty

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


logger = logging.getLogger(__name__)


class MyEventHandler(FileSystemEventHandler):

    def __init__(self, event_queue):
        super().__init__()
        self._event_queue = event_queue

    def on_any_event(self, event):
        self._event_queue.put({"source": "FileDetector", "event":event})


class FileSystemEventDetector(object):

    def __init__(self, event_queue):
        self._path = "/home/gyuri/Asztal/sync_dir"
        self._event_handler = MyEventHandler(event_queue)
        self._observer = Observer()
    
    def run(self):
        logger.info("Starting file detector")
        self._observer.schedule(self._event_handler, self._path, recursive=True)
        self._observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping file detector")
            self._observer.stop()
        self._observer.join()
