import logging
import re
from os import unlink
from queue import Queue

import control.cli
from .abstract import Singleton
from control.account import CloudAPIFactory

from model.message import NetworkMessage, NetworkMessageHeader, MessageTypes
from model.file import FileData, FileStatuses, CloudFilesCache
from model.account import AccountData


moduleLogger = logging.getLogger(__name__)


class MessageDispatcher(metaclass=Singleton):

    __INSTANT_TASK_TYPES = [MessageTypes.GET_ACCOUNT_LIST, MessageTypes.SET_ACCOUNT_LIST, MessageTypes.SYNC_FILES, MessageTypes.GET_WORKSPACE, MessageTypes.MOVE_FILE, MessageTypes.DELETE_FILE]
    __SLOW_TASK_TYPES = [MessageTypes.UPLOAD_FILE, MessageTypes.DOWNLOAD_FILE]

    def __init__(self):
        self.incoming_instant_task_queue = Queue()
        self.incoming_task_queue = Queue()
        self.outgoing_message_queue = Queue()

        self._logger = moduleLogger.getChild("MessageDispatcher")

    def dispatchIncomingMessage(self, message):
        messageType = message.header.messageType

        if messageType in self.__INSTANT_TASK_TYPES:
            self.incoming_instant_task_queue.put(message)
        elif messageType in self.__SLOW_TASK_TYPES:
            self.incoming_task_queue.put(message)
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

    def __init__(self, *args):
        super().__init__(*args)
        self.__cloudAccounts = [CloudAPIFactory.fromAccountData(accData) for accData in self._databaseAccess.getAllAccounts()]
        self.__partPattern = "(__[0-9]+){2}\.enc"
        self.__totalCountPattern = "__[0-9]+"
        self.__filesCache = CloudFilesCache()

    def _getLogger(self):
        return moduleLogger.getChild("GetFileListHandler")

    def handle(self):
        self._logger.debug("Retrieving file list")

        fileList = {}
        for account in self.__cloudAccounts:
            self.__processAccountFiles(account.getFileList(), account.accountData.id)

        fullFiles = self.__filesCache.getFullFiles()
        incompleteFiles = self.__filesCache.getIncompleteFiles()
        self._logger.debug(f"Found the following full files: {fullFiles}")
        self._logger.warning(f"The following files have missing parts: {incompleteFiles}")

        self.__sendResponse(fullFiles)
        self._task = None

    def __processAccountFiles(self, files, accountID):
        for filePart in files:
            self.__filesCache.insertFilePart(filePart, accountID)

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


class UploadFileHandler(AbstractTaskHandler):

    def _getLogger(self):
        return moduleLogger.getChild("UploadFileHandler")

    def handle(self):
        accounts = self._databaseAccess.getAllAccounts()

        perAccountSize = self._task.data['size'] / len(accounts)
        localFilePath = f"{control.cli.CONSOLE_ARGUMENTS.workspace}/server/{self._task.uuid}"

        with open(localFilePath, "rb") as localFileHandle:
            if perAccountSize < 1.0 or len(accounts) == 1:
                self.__uploadToFirstAccountOnly(accounts[0], localFileHandle)
            else:
                self.__uploadToAllAccounts(accounts, localFileHandle)

        self.__cleanUp(localFilePath)
        self.__sendResponse()
        self._task = None

    def __cleanUp(self, localFilePath):
        unlink(localFilePath)

    def __sendResponse(self):
        if not self._task.stale:
            data = {"sourcePath": self._task.data["fullPath"], "status": FileStatuses.SYNCED}
            response = NetworkMessage.Builder(MessageTypes.FILE_STATUS_UPDATE).withData(data).withRandomUUID().build()
            self._messageDispatcher.dispatchResponse(response)

    def __uploadToFirstAccountOnly(self, account, fileHandle):
        cloudAccount = CloudAPIFactory.fromAccountData(account)
        cloudFileName = f"{self._task.data['filename']}__1__1.enc"
        cloudAccount.upload(fileHandle, self._task.data['size'], cloudFileName, self._task)

    def __uploadToAllAccounts(self, accounts, fileHandle):
        pass
