import logging
import re

from queue import Queue

from .abstract import Singleton

from control.account import SFTPCloudAccount

from model.message import NetworkMessage, NetworkMessageHeader, MessageTypes
from model.file import FileData
from model.account import AccountData


moduleLogger = logging.getLogger(__name__)


class MessageDispatcher(metaclass=Singleton):

    def __init__(self):
        self.incoming_instant_task_queue = Queue()
        self.incoming_task_queue = Queue()
        self.outgoing_message_queue = Queue()

        self._logger = moduleLogger.getChild("MessageDispatcher")

    def dispatchIncomingMessage(self, message):
        if message.header.messageType in [MessageTypes.GET_ACCOUNT_LIST, MessageTypes.SET_ACCOUNT_LIST, MessageTypes.SYNC_FILES]:
            self.incoming_instant_task_queue.put(message)
        else:
            self._logger.warning(f"Unknown message: {message}")

    def dispatchResponse(self, message):
        self.outgoing_message_queue.put(message)


class AbstractTaskHandler():

    def __init__(self, databaseAccess):
        self._task = None
        self._logger = self._getLogger()
        self._databaseAccess = databaseAccess
        self._messageDispatcher = MessageDispatcher()

    def _getLogger(self):
        raise NotImplementedError("Derived class should implement method '_getLogger'!")

    def setTask(self, task):
        self._task = task


class GetAccountsListHandler(AbstractTaskHandler):

    def _getLogger(self):
        return moduleLogger.getChild("GetAccountListHandler")

    def handle(self):
        rawHeader = {"messageType": MessageTypes.RESPONSE, "uuid": self._task.uuid}
        rawData = {"accounts": [acc.serialize() for acc in self._databaseAccess.getAllAccounts()]}

        response = NetworkMessage({"header": rawHeader, "data": rawData})
        self._logger.debug(f"Sending response: {rawHeader},  {rawData}")
        self._messageDispatcher.dispatchResponse(response)
        self._task = None


class SetAccountListHandler(AbstractTaskHandler):

    def _getLogger(self):
        return moduleLogger.getChild("SetAccountListHandler")

    def handle(self):
        self._logger.debug("Updating account list")
        currentAccounts = {acc.id: acc.identifier for acc in self._databaseAccess.getAllAccounts()}
        newAccounts = [AccountData(id=raw.get('id', None), identifier=raw['identifier'], accountType=raw['accountType'], cryptoKey=raw['cryptoKey'], data=raw['data']) for raw in self._task.data['accounts']]
        newAccountIDs = [acc.id for acc in newAccounts]

        for accID, accName in currentAccounts.items():
            if accID not in newAccountIDs:
                self._logger.debug(f"Deleting account: {accName}(ID: {accID})")
                self._databaseAccess.deleteAccount(accID)

        for account in newAccounts:
            self._databaseAccess.createOrUpdateAccount(account)

        self._databaseAccess.commit()
        self._logger.debug("Accounts updated")


class GetFileListHandler(AbstractTaskHandler):
    # TEMPORARY
    __accounts = [
        {"username": "cloudAccount1", "password": "ferius123"},
        {"username": "cloudAccount2", "password": "ferius123"}
    ]

    def __init__(self, *args):
        super().__init__(*args)
        self.__cloudAccounts = [
            SFTPCloudAccount(self.__accounts[0]),
            SFTPCloudAccount(self.__accounts[1])
        ]
        self.__partPattern = "(__[0-9]+){2}\.enc"
        self.__totalCountPattern = "__[0-9]+"

    def _getLogger(self):
        return moduleLogger.getChild("GetFileListHandler")

    def handle(self):
        self._logger.debug("Retrieving file list")

        fileList = {}
        for account in self.__cloudAccounts:
            accountFileList = account.getFileList()
            for filePart in accountFileList:
                filename = self.__getRealFilename(filePart.filename)
                if filePart.fullPath not in fileList:
                    fileList[filePart.fullPath] = {"data": filePart, "availableCount": 1, "totalCount": self.__getFilePartCount(filePart.filename)}
                    fileList[filePart.fullPath]["data"].filename = filename
                else:
                    fileList[filePart.fullPath]["data"].size += filePart.size
                    fileList[filePart.fullPath]["availableCount"] += 1
        fullFiles = [remoteFile["data"].serialize() for key, remoteFile in fileList.items() if remoteFile["availableCount"] == remoteFile["totalCount"]]
        self._logger.debug(f"Found the following full files: {fullFiles}")

        self.__sendResponse(fullFiles)
        self._task = None

    def __getRealFilename(self, filePartName):
        match = re.search(self.__partPattern, filePartName)
        matchStartIndex = match.span()[0]

        return filePartName[:matchStartIndex]

    def __getFilePartCount(self, filePartName):
        match = re.findall(self.__totalCountPattern, filePartName)

        return int(match[1].split("__")[1])

    def __sendResponse(self, fullFiles):
        raw = {"header": {"messageType": MessageTypes.RESPONSE, "uuid": self._task.uuid}, "data": fullFiles}
        response = NetworkMessage(raw)

        self._messageDispatcher.dispatchResponse(response)
