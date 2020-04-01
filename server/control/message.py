import logging

from queue import Queue

from .abstract import Singleton
from model.message import NetworkMessage, NetworkMessageHeader, MessageTypes


moduleLogger = logging.getLogger(__name__)


class MessageDispatcher(metaclass=Singleton):

    def __init__(self):
        self.incoming_instant_task_queue = Queue()
        self.incoming_task_queue = Queue()
        self.outgoing_message_queue = Queue()

        self._logger = moduleLogger.getChild("MessageDispatcher")


class AbstractTaskHandler():

    def __init__(self):
        self._task = None
        self._logger = self._getLogger()
        self._messageDispatcher = MessageDispatcher()

    def _getLogger(self):
        raise NotImplementedError("Derived class should implement method '_getLogger'!")

    def setTask(self, task):
        self._task = task


class GetAccountsListHandler(AbstractTaskHandler):

    def __init__(self, databaseAccess):
        super().__init__()
        self.__databaseAccess = databaseAccess

    def _getLogger(self):
        return moduleLogger.getChild("MessageDispatcher")

    def handle(self):
        rawHeader = {"messageType": MessageTypes.RESPONSE, "uuid": self._task.uuid}
        rawData = {"accounts": [acc.serialize() for acc in self.__databaseAccess.getAllAccounts()]}

        response = NetworkMessage({"header": rawHeader, "data": rawData})
        self._logger.debug("Sending response: {rawHeader},  {rawData}")
        self._messageDispatcher.outgoing_message_queue.put(response)
        self._task = None
