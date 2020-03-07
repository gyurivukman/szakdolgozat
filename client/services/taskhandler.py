import logging
from time import sleep
from multiprocessing import Queue
from threading import Thread
from queue import Empty

from .network import NetworkClient
from .filestorage import FileStorage


class TaskMaster(object):

    def __init__(self):
        self._service = {}
        self._shouldRun = True
        self._logger = logging.getLogger(__name__)
        self._serviceThreadPool = {}

    def run(self):
        self._logger.info("Starting Taskhandler service")
        self._initNetwork()
        self._initFileStorage()
        self._startNetwork()
        self._startFileStorage()

        while self._shouldRun:
            self._readQueue(self._serviceThreadPool['network']['queue'])
            self._readQueue(self._serviceThreadPool['fileStorage']['queue'])
        self._shutdownNetwork()
        self._shutdownFileStorage()

    def stop(self):
        self._shouldRun = False

    def _initNetwork(self):
        self._serviceThreadPool['network'] = {'thread': None, 'service': None, 'queue': Queue()}
        self._serviceThreadPool['network']['service'] = NetworkClient(self._serviceThreadPool['network']['queue'])
        self._serviceThreadPool['network']['thread'] = Thread(target=self._serviceThreadPool['network']['service'].run)

    def _startNetwork(self):
        self._serviceThreadPool['network']['thread'].start()

    def _shutdownNetwork(self):
        self._serviceThreadPool['network']['service'].stop()
        self._serviceThreadPool['network']['thread'].join()

    def _initFileStorage(self):
        self._serviceThreadPool['fileStorage'] = {'thread': None, 'service': None, 'queue': Queue()}
        self._serviceThreadPool['fileStorage']['service'] = FileStorage(self._serviceThreadPool['fileStorage']['queue'])
        self._serviceThreadPool['fileStorage']['thread'] = Thread(target=self._serviceThreadPool['fileStorage']["service"].run)

    def _startFileStorage(self):
        self._serviceThreadPool['fileStorage']['thread'].start()

    def _shutdownFileStorage(self):
        self._serviceThreadPool['fileStorage']['service'].stop()
        self._serviceThreadPool['fileStorage']['thread'].join()

    def _readQueue(self, queue):
        try:
            message = queue.get_nowait()
            logging.info(message)
            self._serviceThreadPool['fileStorage']['service'].kukken()
        except Empty:
            pass
