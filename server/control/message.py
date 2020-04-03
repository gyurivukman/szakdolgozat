import logging

from queue import Queue

from .abstract import Singleton
from model.message import NetworkMessage, NetworkMessageHeader, MessageTypes
from model.account import AccountData


moduleLogger = logging.getLogger(__name__)


class MessageDispatcher(metaclass=Singleton):

    def __init__(self):
        self.incoming_instant_task_queue = Queue()
        self.incoming_task_queue = Queue()
        self.outgoing_message_queue = Queue()

        self._logger = moduleLogger.getChild("MessageDispatcher")

    def dispatchMessage(self, message):
        if message.header.messageType in [MessageTypes.GET_ACCOUNT_LIST, MessageTypes.SET_ACCOUNT_LIST]:
            self.incoming_instant_task_queue.put(message)
        else:
            self._logger.warning(f"Unknown message: {message}")


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
        return moduleLogger.getChild("GetAccountListHandler")

    def handle(self):
        rawHeader = {"messageType": MessageTypes.RESPONSE, "uuid": self._task.uuid}
        rawData = {"accounts": [acc.serialize() for acc in self.__databaseAccess.getAllAccounts()]}

        response = NetworkMessage({"header": rawHeader, "data": rawData})
        self._logger.debug(f"Sending response: {rawHeader},  {rawData}")
        self._messageDispatcher.outgoing_message_queue.put(response)
        self._task = None


class SetAccountListHandler(AbstractTaskHandler):

    def __init__(self, databaseAccess):
        super().__init__()
        self.__databaseAccess = databaseAccess

    def _getLogger(self):
        return moduleLogger.getChild("SetAccountListHandler")

    def handle(self):
        self._logger.debug("Updating account list")
        currentAccounts = {acc.id: acc.identifier for acc in self.__databaseAccess.getAllAccounts()}
        newAccounts = [AccountData(id=raw.get('id', None), identifier=raw['identifier'], accountType=raw['accountType'], cryptoKey=raw['cryptoKey'], data=raw['data']) for raw in self._task.data['accounts']]
        newAccountIDs = [acc.id for acc in newAccounts]

        for accID, accName in currentAccounts.items():
            if accID not in newAccountIDs:
                self._logger.debug(f"Deleting account: {accName}(ID: {accID})")
                self.__databaseAccess.deleteAccount(accID)

        for account in newAccounts:
            self.__databaseAccess.createOrUpdateAccount(account)

        self.__databaseAccess.commit()
        self._logger.debug("Accounts updated")
