import logging
import re

from queue import Queue

from .abstract import Singleton

from control.account import CloudAPIFactory
import control.cli

from model.message import NetworkMessage, NetworkMessageHeader, MessageTypes
from model.file import FileData
from model.account import AccountData


moduleLogger = logging.getLogger(__name__)


class MessageDispatcher(metaclass=Singleton):

    __INSTANT_TASK_TYPES = [MessageTypes.GET_ACCOUNT_LIST, MessageTypes.SET_ACCOUNT_LIST, MessageTypes.SYNC_FILES, MessageTypes.GET_WORKSPACE]

    def __init__(self):
        self.incoming_instant_task_queue = Queue()
        self.incoming_task_queue = Queue()
        self.outgoing_message_queue = Queue()

        self._logger = moduleLogger.getChild("MessageDispatcher")

    def dispatchIncomingMessage(self, message):
        if message.header.messageType in self.__INSTANT_TASK_TYPES:
            self.incoming_instant_task_queue.put(message)
        # TODO elif message.header.messageType in self.__SLOW_TASK_TYPES:
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
        data = {"accounts": [acc.serialize() for acc in self._databaseAccess.getAllAccounts()]}

        response = NetworkMessage.Builder(MessageTypes.RESPONSE).withUUID(self._task.uuid).withData(data).build()
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

        response = NetworkMessage.Builder(MessageTypes.RESPONSE).withUUID(self._task.uuid).build()
        self._messageDispatcher.dispatchResponse(response)


class GetFileListHandler(AbstractTaskHandler):
    # TEMPORARY

    def __init__(self, *args):
        super().__init__(*args)
        self.__cloudAccounts = [CloudAPIFactory.fromAccountData(accData) for accData in self._databaseAccess.getAllAccounts()]
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
                realFilename = self.__getRealFilename(filePart.filename)
                filePart.fullPath = f"{filePart.path}/{realFilename}" if len(filePart.path) > 0 else realFilename
                if filePart.fullPath not in fileList:
                    fileList[filePart.fullPath] = {"data": filePart, "availableCount": 1, "totalCount": self.__getFilePartCount(filePart.filename), "storingAccountIDs": [account.accountData.id]}
                    fileList[filePart.fullPath]["data"].filename = realFilename
                else:
                    fileList[filePart.fullPath]["data"].size += filePart.size
                    fileList[filePart.fullPath]["availableCount"] += 1
                    fileList[filePart.fullPath]["storingAccountIDs"].append(account.accountData.id)
        fullFiles = [remoteFile["data"].serialize() for key, remoteFile in fileList.items() if remoteFile["availableCount"] == remoteFile["totalCount"]]
        partsMissing = [f"{remoteFile['data'].fullPath} (missing part count: {remoteFile['totalCount'] - remoteFile['availableCount']})" for key, remoteFile in fileList.items() if remoteFile['totalCount'] > remoteFile['availableCount']]
        self._logger.debug(f"Found the following full files:{[{'file:': remoteFile['data'].serialize(), 'storingAccountIDs':remoteFile['storingAccountIDs']} for key, remoteFile in fileList.items() if remoteFile['availableCount'] == remoteFile['totalCount']] }")
        self._logger.warning(f"The following files have missing parts: {partsMissing}")

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
        response = NetworkMessage.Builder(MessageTypes.RESPONSE).withUUID(self._task.uuid).withData(fullFiles).build()
        self._messageDispatcher.dispatchResponse(response)


class GetWorkspaceHandler(AbstractTaskHandler):

    def _getLogger(self):
        return moduleLogger.getChild("GetWorkspaceHandler")

    def handle(self):
        data = {"workspace": control.cli.CONSOLE_ARGUMENTS.workspace}

        response = NetworkMessage.Builder(MessageTypes.RESPONSE).withUUID(self._task.uuid).withData(data).build()
        self._messageDispatcher.dispatchResponse(response)
        self._task = None
