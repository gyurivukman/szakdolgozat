import logging

from queue import Queue


class MessageDispatcher(object):
    __instance = None

    def __init__(self):
        if MessageDispatcher.__instance is not None:
            raise Exception("This class is a singleton! use MessageDispatcher.getInstance() instead!")
        else:
            MessageDispatcher.__instance = self

            self.incoming_instant_task_queue = Queue()
            self.incoming_task_queue = Queue()
            self.outgoing_task_queue = Queue()

            self._logger = logging.getLogger(__name__).getChild("MessageDispatcher")

    @staticmethod
    def getInstance():
        if MessageDispatcher.__instance is None:
            MessageDispatcher()
        return MessageDispatcher.__instance
