import logging
import re
import os
from math import ceil
from queue import Queue

import control.cli
from .abstract import Singleton
from control.account import CloudAPIFactory
from control.util import chunkSizeGenerator

from model.message import NetworkMessage, NetworkMessageHeader, MessageTypes
from model.file import FileData, FileStatuses, CloudFilesCache
from model.account import AccountData
from model.task import TaskArchive, Task


moduleLogger = logging.getLogger(__name__)


class MessageDispatcher(metaclass=Singleton):

    __INSTANT_TASK_TYPES = [
        MessageTypes.GET_ACCOUNT_LIST, MessageTypes.SET_ACCOUNT_LIST,
        MessageTypes.SYNC_FILES, MessageTypes.GET_WORKSPACE,
        MessageTypes.MOVE_FILE, MessageTypes.DELETE_FILE,
    ]
    __SLOW_TASK_TYPES = [MessageTypes.UPLOAD_FILE, MessageTypes.DOWNLOAD_FILE]

    def __init__(self):
        self.incoming_instant_task_queue = Queue()
        self.incoming_task_queue = Queue()
        self.outgoing_message_queue = Queue()

        self._logger = moduleLogger.getChild("MessageDispatcher")
        self.__longFileTaskArchive = TaskArchive()

    def dispatchIncomingMessage(self, message):
        messageType = message.header.messageType
        task = Task(taskType=messageType, stale=False, uuid=message.header.uuid, data=message.data)

        if messageType in self.__INSTANT_TASK_TYPES:
            if messageType == MessageTypes.DELETE_FILE:
                path = message.data["fullPath"]
                self.__longFileTaskArchive.cancelTask(path)
                self.__longFileTaskArchive.removeTask(path)
            elif messageType == MessageTypes.MOVE_FILE:
                self.__longFileTaskArchive.cancelTask(message.data["source"])
                self.__longFileTaskArchive.cancelTask(message.data["target"]["fullPath"])

                self.__longFileTaskArchive.removeTask(message.data["source"])
                self.__longFileTaskArchive.removeTask(message.data["target"]["fullPath"])
            self.incoming_instant_task_queue.put(task)
        elif messageType in self.__SLOW_TASK_TYPES:
            key = task.data["fullPath"]
            self.__longFileTaskArchive.addTask(key, task)
            self.incoming_task_queue.put(task)
        elif messageType == MessageTypes.FILE_TASK_CANCELLED:
            self._logger.debug(f"Cancelling task for file: {message.data['fullPath']}")
            self.__longFileTaskArchive.cancelTask(message.data["fullPath"])
            self.__longFileTaskArchive.removeTask(message.data["fullPath"])
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
        self._filesCache = CloudFilesCache()
        self._taskArchive = TaskArchive()

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
        self.__totalCountPattern = "__[0-9]+"
        self._filesCache = CloudFilesCache()

    def _getLogger(self):
        return moduleLogger.getChild("GetFileListHandler")

    def handle(self):
        self._logger.debug("Retrieving file list")

        self._filesCache.clearData()
        for account in self.__cloudAccounts:
            self.__processAccountFiles(account.getFileList())

        fullFiles = self._filesCache.getFullFiles()
        incompleteFiles = self._filesCache.getIncompleteFiles()
        self._logger.debug(f"Found the following full files: {fullFiles}")
        if incompleteFiles:
            incompleteFilesMessage = "\n".join([f"{cachedFile.data.fullPath} (missing part count: {cachedFile.totalPartCount - cachedFile.availablePartCount})" for cachedFile in incompleteFiles])
            self._logger.warning(f"The following files have missing parts:\n{incompleteFilesMessage}")

        self.__sendResponse(fullFiles)
        self._task = None

    def __processAccountFiles(self, fileParts):
        for filePart in fileParts:
            self._filesCache.insertFilePart(filePart)

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

        perAccountSize = ceil(self._task.data["size"] / len(accounts))
        localFilePath = f"{control.cli.CONSOLE_ARGUMENTS.workspace}/server/{self._task.uuid}"
        cachedFile = self._filesCache.getFile(self._task.data["fullPath"])

        with open(localFilePath, "rb") as localFileHandle:
            if len(accounts) == 1 or perAccountSize <= 1.0:
                self._logger.info(f"Uploading to single account only: {self._task.data['fullPath']}")
                self.__uploadToFirstAccountOnly(accounts[0], localFileHandle, cachedFile)
            else:
                self.__uploadToAllAccounts(accounts, perAccountSize, localFileHandle, cachedFile)

        self.__cleanUp(localFilePath)
        if not self._task.stale:
            self.__sendResponse()
        else:
            self._logger.info(f"Task '{self._task}' cancelled, not sending response.")
        self._task = None

    def __cleanUp(self, localFilePath):
        os.unlink(localFilePath)

    def __sendResponse(self):
        if not self._task.stale:
            data = {"fullPath": self._task.data["fullPath"], "filename": self._task.data["filename"], "modified": self._task.data["utcModified"], "size": self._task.data["size"], "path": self._task.data["path"], "status": FileStatuses.SYNCED}
            response = NetworkMessage.Builder(MessageTypes.FILE_STATUS_UPDATE).withData(data).withRandomUUID().build()
            self._messageDispatcher.dispatchResponse(response)

    def __cleanFromRemote(self, cachedFile):
        storedParts = {partInfo.storingAccountID: partInfo for partName, partInfo in cachedFile.parts.items()}
        cloudAccounts = [CloudAPIFactory.fromAccountData(account) for account in self._databaseAccess.getAllAccounts() if account.id in storedParts]
        for account in cloudAccounts:
            account.deleteFile(storedParts[account.accountData.id])

    def __uploadToFirstAccountOnly(self, account, fileHandle, cachedFile):
        if not self._task.stale:
            if cachedFile:
                self.__cleanFromRemote(cachedFile)
                self._filesCache.removeFile(cachedFile.data.fullPath)

            cloudAccount = CloudAPIFactory.fromAccountData(account)
            cloudFileName = f"{self._task.data['filename']}__1__1.enc"
            result = cloudAccount.upload(fileHandle, self._task.data['size'], cloudFileName, self._task)
            if result:
                self.__updateFilesCache(result)

    def __uploadToAllAccounts(self, accounts, perAccountSize, fileHandle, cachedFile):
        if not self._task.stale:
            if cachedFile:
                self.__cleanFromRemote(cachedFile)
                self._filesCache.removeFile(cachedFile.data.fullPath)

        totalCount = len(accounts)
        for account, partIndex, toUploadChunkInfo in zip(accounts, range(totalCount), chunkSizeGenerator(self._task.data["size"], perAccountSize)):
            if not self._task.stale:
                cloudAccount = CloudAPIFactory.fromAccountData(account)
                cloudFileName = f"{self._task.data['filename']}__{partIndex + 1}__{totalCount}.enc"
                result = cloudAccount.upload(fileHandle, toUploadChunkInfo[0], cloudFileName, self._task)
                if result:
                    self._logger.debug(f"Updating cache with result: {result}")
                    self.__updateFilesCache(result)

    def __updateFilesCache(self, resultingFilePart):
        self._logger.debug(f"Updating file cache with a new file: {resultingFilePart.fullPath}")
        self._filesCache.insertFilePart(resultingFilePart)
        self._logger.debug(f"Inserted new file to cache after upload, from part: {resultingFilePart}")

    def __updateAlreadyExistingEntry(self, cachedFile, resultingFilePart):
        cachedFile.parts[resultingFilePart.filename] = resultingFilePart


class DownloadFileHandler(AbstractTaskHandler):

    def _getLogger(self):
        return moduleLogger.getChild("DownloadFileHandler")

    def handle(self):
        localFilePath = f"{control.cli.CONSOLE_ARGUMENTS.workspace}/server/{self._task.uuid}"
        targetFilePath = f"{control.cli.CONSOLE_ARGUMENTS.workspace}/client/{self._task.uuid}"
        cachedFileInfo = self._filesCache.getFile(self._task.data["fullPath"])
        parts = [part for key, part in cachedFileInfo.parts.items()]
        parts.sort(key=lambda part: part.filename)
        storingAccounts = {account.id: account for account in self._databaseAccess.getAllAccounts() if account.id in [part.storingAccountID for part in parts]}

        self._logger.debug(f"Downloading file '{cachedFileInfo.data.fullPath}' from accounts: {[acc.identifier for key, acc in storingAccounts.items()]}")
        self._logger.debug(f"Sorted parts: {parts}")

        with open(localFilePath, "wb") as outputFileHandle:
            for part in parts:
                cloudAccount = CloudAPIFactory.fromAccountData(storingAccounts[part.storingAccountID])
                self._logger.debug(f"Downloading part {part.filename} from {cloudAccount.accountData.identifier}")
                cloudAccount.download(outputFileHandle, part, self._task)
        self._logger.debug("Download finished, moving file to client workspace...")
        self.__finalizeDownload(localFilePath, targetFilePath)
        self._task = None

    def __finalizeDownload(self, localPath, targetPath):
        if not self._task.stale:
            os.rename(localPath, targetPath)
            self.__sendResponse()
        else:
            os.remove(localPath)

    def __sendResponse(self):
        data = self._task.data
        data["status"] = FileStatuses.DOWNLOADING_TO_LOCAL

        response = NetworkMessage.Builder(MessageTypes.FILE_STATUS_UPDATE).withData(data).withUUID(self._task.uuid).build()
        self._messageDispatcher.dispatchResponse(response)


class DeleteFileHandler(AbstractTaskHandler):

    def handle(self):
        toDeletePath = self._task.data["fullPath"]
        dbAccounts = {acc.id: acc for acc in self._databaseAccess.getAllAccounts()}
        cachedFileInfo = self._filesCache.getFile(toDeletePath)
        if cachedFileInfo:
            for partName, part in cachedFileInfo.parts.items():
                self._logger.debug(f"Removing part: {partName} from accountID: {part.storingAccountID}")
                cloudAccount = CloudAPIFactory.fromAccountData(dbAccounts[part.storingAccountID])
                cloudAccount.deleteFile(part)
            self._filesCache.removeFile(toDeletePath)

    def _getLogger(self):
        return moduleLogger.getChild("DeleteFileHandler")


class MoveFileHandler(AbstractTaskHandler):

    def __init__(self, *args):
        super().__init__(*args)
        self.__partPattern = "(__[0-9]+){2}\.enc"

    def handle(self):
        # targetPath has to be deleted if exists. No matter the parts.
        cachedTargetFile = self._filesCache.getFile(self._task.data["target"]["fullPath"])
        if cachedTargetFile:
            self._logger.info("Pre-cleaning target file parts")
            self.__cleanFromRemote(cachedTargetFile)
            self._filesCache.removeFile(self._task.data["target"]["fullPath"])

        targetFileData = self._task.data["target"]
        cachedSourceFile = self._filesCache.getFile(self._task.data["source"])
        responseData = None

        # if sourcePath is synced, simple move and respond with moved, else delete sourcePath and respond with reupload.
        if self.__isSourceSynced(cachedSourceFile, targetFileData):
            self.__moveFile(cachedSourceFile, targetFileData)
            responseData = {"moveSuccessful": True, "from": self._task.data["source"], "to": targetFileData["fullPath"]}
        else:
            if cachedSourceFile:
                self.__cleanFromRemote(cachedSourceFile)
                self._filesCache.removeFile(cachedSourceFile.data.fullPath)
            responseData = {"moveSuccessful": False, "from": self._task.data["source"], "to": targetFileData["fullPath"]}
        response = NetworkMessage.Builder(MessageTypes.RESPONSE).withUUID(self._task.uuid).withData(responseData).build()
        self._messageDispatcher.dispatchResponse(response)
        self._task = None

    def _getLogger(self):
        return moduleLogger.getChild("MoveFileHandler")

    def __cleanFromRemote(self, cachedFile):
        storedParts = {partInfo.storingAccountID: partInfo for partName, partInfo in cachedFile.parts.items()}
        cloudAccounts = [CloudAPIFactory.fromAccountData(account) for account in self._databaseAccess.getAllAccounts() if account.id in storedParts]
        for account in cloudAccounts:
            account.deleteFile(storedParts[account.accountData.id])

    def __isSourceSynced(self, cachedSourceFile, movedFile):
        return cachedSourceFile and cachedSourceFile.availablePartCount == cachedSourceFile.totalPartCount and cachedSourceFile.data.modified == self._task.data["target"]["modified"]

    def __moveFile(self, cachedSourceFile, movedFileData):
        storedParts = {partInfo.storingAccountID: partInfo for partName, partInfo in cachedSourceFile.parts.items()}
        cloudAccounts = [CloudAPIFactory.fromAccountData(account) for account in self._databaseAccess.getAllAccounts() if account.id in storedParts]

        for account in cloudAccounts:
            part = storedParts[account.accountData.id]  # alma__1__2.enc
            newPartName = self.__getNewPartName(part.filename, movedFileData["filename"])
            newPartFullPath = f"{movedFileData['path']}/{newPartName}" if len(movedFileData['path']) > 0 else newPartName
            account.moveFile(part, newPartFullPath)
            part.path = movedFileData["path"]
            part.fullPath = newPartFullPath
        cachedSourceFile.data.path = movedFileData["path"]
        cachedSourceFile.data.fullPath = movedFileData["fullPath"]
        self._filesCache.moveFile(self._task.data["source"], movedFileData["fullPath"])

    def __getNewPartName(self, partName, targetFileName):
        match = re.search(self.__partPattern, partName)
        matchStartIndex = match.span()[0]
        partPostFix = partName[matchStartIndex:]
        newPartName = f"{targetFileName}{partPostFix}"

        return newPartName
