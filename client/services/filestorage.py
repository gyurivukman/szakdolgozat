import time
import logging

from multiprocessing import Process

from .filedetector import FileSystemEventDetector


logger = logging.getLogger(__name__)


class FileStorage(object):
    
    def __init__(self, eventQueue):
        self._shouldRun = True
        self._eventQueue = eventQueue
        self._scanner = None
        self._process = Process(target=self._initFileScanner, args=(eventQueue,))
    
    def _initFileScanner(self, eventQueue):
        self._scanner = FileSystemEventDetector(eventQueue)
        self._scanner.run()
    
    def run(self):
        self._process.start()
        self._process.join()

    def stop(self):
        logger.info("Filestorage stopping")
        self._shouldRun = False
    
    def kukken(self):
        print("KUKKEN CALL")