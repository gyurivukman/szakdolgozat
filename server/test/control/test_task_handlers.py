import unittest

from unittest.mock import patch, MagicMock, PropertyMock
from uuid import uuid4


from io import BytesIO
import control.cli
from control.message import *
from control.account import CloudAPIFactory
from model.account import AccountData, AccountTypes
from model.task import Task
from model.message import MessageTypes
from model.file import FilePart, CloudFilesCache, CachedFileData, FileData


class TestGetAccountsListHandler(unittest.TestCase):

    @patch("control.database.DatabaseAccess")
    def setUp(self, fakeDB):
        self.fakeDB = fakeDB
        self.testHandler = GetAccountsListHandler(fakeDB)

    @patch.object(MessageDispatcher, "dispatchResponse")
    def test_handler_retrieves_accounts_from_database_and_sends_response(self, dispatchResponseMock):
        testAccounts = [AccountData(id=1, identifier="testAccountID", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken"})]
        testTask = Task(taskType=MessageTypes.GET_ACCOUNT_LIST, uuid=uuid4().hex)

        self.fakeDB.getAllAccounts.return_value = testAccounts

        self.testHandler.setTask(testTask)
        self.testHandler.handle()

        self.assertEqual(self.fakeDB.getAllAccounts.call_count, 1)

        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.uuid, testTask.uuid)

        self.assertEqual(type(dispatchResponseMock.call_args[0][0].data["accounts"]), list)
        self.assertEqual(len(dispatchResponseMock.call_args[0][0].data["accounts"]), len(testAccounts))

        self.assertEqual(dispatchResponseMock.call_args[0][0].data["accounts"][0], testAccounts[0].serialize())


class TestSetAccountListHandler(unittest.TestCase):

    @patch("control.database.DatabaseAccess")
    def setUp(self, fakeDB):
        self.fakeDB = fakeDB
        self.testHandler = SetAccountListHandler(fakeDB)

    @patch.object(MessageDispatcher, "dispatchResponse")
    def test_set_account_list_handler_sets_accounts_and_returns_response(self, dispatchResponseMock):
        testAccounts = {"accounts": [AccountData(id=1, identifier="testAccountID", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken"}).serialize()]}
        testTask = Task(taskType=MessageTypes.SET_ACCOUNT_LIST, uuid=uuid4().hex, data=testAccounts)

        self.testHandler.setTask(testTask)
        self.testHandler.handle()

        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_count, 1)
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].id, testAccounts["accounts"][0]["id"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].identifier, testAccounts["accounts"][0]["identifier"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].accountType, testAccounts["accounts"][0]["accountType"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].cryptoKey, testAccounts["accounts"][0]["cryptoKey"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].data, testAccounts["accounts"][0]["data"])

        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.uuid, testTask.uuid)


class TestGetFileListHandler(unittest.TestCase):

    @patch("control.database.DatabaseAccess")
    def setUp(self, fakeDB):
        self.fakeDB = fakeDB

    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch.object(MessageDispatcher, "dispatchResponse")
    def test_get_file_list_returns_all_non_full_files(self, dispatchResponseMock, fakeAPIFactory):

        fakeCloudAPI = MagicMock()
        fakeGetFileListResponse = [
            FilePart(filename="full_file__1__1.enc", modified=1, size=32, path="", fullPath="full_file__1__1.enc", storingAccountID=1),
            FilePart(filename="partial_file__1__2.enc", modified=1, size=48, path="subDir", fullPath="subDir/partial_file__1__2.enc", storingAccountID=1)
        ]
        fakeCloudAPI.getFileList.return_value = fakeGetFileListResponse

        self.fakeDB.getAllAccounts.return_value = [AccountData(id=1, identifier="testAccountID", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken"})]
        fakeAPIFactory.return_value = fakeCloudAPI
        testTask = Task(taskType=MessageTypes.SYNC_FILES, uuid=uuid4().hex)

        testHandler = GetFileListHandler(self.fakeDB)
        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(fakeCloudAPI.getFileList.call_count, 1)
        self.assertEqual(fakeAPIFactory.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.uuid, testTask.uuid)

        self.assertEqual(len(dispatchResponseMock.call_args[0][0].data), 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data[0]["filename"], "full_file")
        self.assertEqual(dispatchResponseMock.call_args[0][0].data[0]["modified"], fakeGetFileListResponse[0].modified)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data[0]["size"], fakeGetFileListResponse[0].size - 16)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data[0]["path"], fakeGetFileListResponse[0].path)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data[0]["fullPath"], "full_file")


class FakeGlobalConsoleArguments:
    def __init__(self, workspace):
        self.workspace = workspace


class TestGetWorkspaceHandler(unittest.TestCase):

    @classmethod
    @patch("control.database.DatabaseAccess")
    def setUpClass(cls, fakeDB):
        cls.fakeDB = fakeDB

    @patch('control.cli.CONSOLE_ARGUMENTS', FakeGlobalConsoleArguments("testWorkspace"))
    @patch.object(MessageDispatcher, "dispatchResponse")
    def test_get_workspace_handler_returns_workspace_path_from_command_line_argument_in_message(self, dispatchResponseMock):
        testTask = Task(taskType=MessageTypes.GET_WORKSPACE, uuid=uuid4().hex)
        testHandler = GetWorkspaceHandler(self.fakeDB)

        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.uuid, testTask.uuid)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data, {"workspace": "testWorkspace"})


class TestUploadFileHandler(unittest.TestCase):

    @classmethod
    @patch("control.database.DatabaseAccess")
    def setUpClass(cls, fakeDB):
        cls.fakeDB = fakeDB

    @patch("control.cli.CONSOLE_ARGUMENTS", FakeGlobalConsoleArguments("testWorkspace"))
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch("os.unlink")
    @patch.object(CloudFilesCache, "getFile")
    @patch.object(CloudFilesCache, "insertFilePart")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch("control.message.open")
    def test_uploads_file_to_single_account_and_cleans_up_server_side_file_and_creates_new_filescache_entry_and_sends_response(self, openMock, cloudApiMock, insertFilePartMock, getFileMock, os_unlinkMock, dispatchResponseMock):
        fakeFile = BytesIO(b"Lorem ipsum")
        openMock.return_value = fakeFile
        fakeAccounts = [AccountData(id=1, identifier="testAccountID", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken"})]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts
        getFileMock.return_value = None

        testTaskData = {"filename": "apple.txt", "size": 11, "fullPath": "subDir/apple.txt", "status": None, "utcModified": 10, "path": "subDir"}
        fakeUploadResult = FilePart(
            filename=testTaskData["filename"], modified=testTaskData["utcModified"],
            size=testTaskData["size"], path=testTaskData["path"],
            fullPath=testTaskData["fullPath"], storingAccountID=fakeAccounts[0].id
        )
        cloudApiMock.return_value.upload.return_value = fakeUploadResult

        testTask = Task(taskType=MessageTypes.UPLOAD_FILE, data=testTaskData, uuid=uuid4().hex)
        testHandler = UploadFileHandler(self.fakeDB)
        testHandler.setTask(testTask)

        testHandler.handle()

        self.assertEqual(openMock.call_count, 1)
        self.assertEqual(openMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")
        self.assertEqual(openMock.call_args[0][1], "rb")

        self.assertEqual(cloudApiMock.call_count, 1)
        self.assertEqual(cloudApiMock.call_args[0][0], fakeAccounts[0])

        self.assertEqual(cloudApiMock.return_value.upload.call_count, 1)
        self.assertEqual(cloudApiMock.return_value.upload.call_args[0][0], fakeFile)
        self.assertEqual(cloudApiMock.return_value.upload.call_args[0][1], testTaskData["size"])
        self.assertEqual(cloudApiMock.return_value.upload.call_args[0][2], f"{testTaskData['filename']}__1__1.enc")

        self.assertEqual(insertFilePartMock.call_count, 1)
        self.assertEqual(insertFilePartMock.call_args[0][0], fakeUploadResult)

        self.assertEqual(getFileMock.call_count, 1)
        self.assertEqual(getFileMock.call_args[0][0], testTaskData["fullPath"])

        self.assertEqual(os_unlinkMock.call_count, 1)
        self.assertEqual(os_unlinkMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")

        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.FILE_STATUS_UPDATE)

        self.assertEqual(dispatchResponseMock.call_args[0][0].data["filename"], testTaskData["filename"])
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["path"], testTaskData["path"])
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["fullPath"], testTaskData["fullPath"])
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["size"], testTaskData["size"])
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["modified"], testTaskData["utcModified"])
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["status"], FileStatuses.SYNCED)

    @patch("control.cli.CONSOLE_ARGUMENTS", FakeGlobalConsoleArguments("testWorkspace"))
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch("os.unlink")
    @patch.object(CloudFilesCache, "getFile")
    @patch.object(CloudFilesCache, "insertFilePart")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch("control.message.open")
    def test_uploads_file_to_first_account_only_if_per_accounts_size_is_smaller_than_or_equal_to_one(self, openMock, cloudApiMock, insertFilePartMock, getFileMock, os_unlinkMock, dispatchResponseMock):
        fakeFile = BytesIO(b"Lorem ipsum")
        openMock.return_value = fakeFile
        fakeAccounts = [
            AccountData(id=1, identifier="testAccountID1", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken1"}),
            AccountData(id=2, identifier="testAccountID2", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken2"})
        ]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts
        getFileMock.return_value = None

        testTaskData = {"filename": "apple.txt", "size": 1, "fullPath": "subDir/apple.txt", "status": None, "utcModified": 10, "path": "subDir"}
        fakeUploadResult = FilePart(
            filename=testTaskData["filename"], modified=testTaskData["utcModified"],
            size=testTaskData["size"], path=testTaskData["path"],
            fullPath=testTaskData["fullPath"], storingAccountID=fakeAccounts[0].id
        )
        fakeCloudAccount1 = MagicMock()
        fakeCloudAccount2 = MagicMock()
        cloudApiMock.side_effect = [fakeCloudAccount1, fakeCloudAccount2]

        testTask = Task(taskType=MessageTypes.UPLOAD_FILE, data=testTaskData, uuid=uuid4().hex)
        testHandler = UploadFileHandler(self.fakeDB)
        testHandler.setTask(testTask)

        testHandler.handle()

        self.assertEqual(fakeCloudAccount1.upload.call_count, 1)
        self.assertEqual(fakeCloudAccount2.upload.call_count, 0)

    @patch("control.cli.CONSOLE_ARGUMENTS", FakeGlobalConsoleArguments("testWorkspace"))
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch("os.unlink")
    @patch.object(CloudFilesCache, "getFile")
    @patch.object(CloudFilesCache, "insertFilePart")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch("control.message.open")
    def test_uploads_file_to_all_accounts_if_per_accounts_size_is_greater_than_one(self, openMock, cloudApiMock, insertFilePartMock, getFileMock, os_unlinkMock, dispatchResponseMock):
        fakeFile = BytesIO(b"Lorem ipsum")
        openMock.return_value = fakeFile
        fakeAccounts = [
            AccountData(id=1, identifier="testAccountID1", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken1"}),
            AccountData(id=2, identifier="testAccountID2", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken2"})
        ]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts
        getFileMock.return_value = None

        testTaskData = {"filename": "apple.txt", "size": 10, "fullPath": "subDir/apple.txt", "status": None, "utcModified": 10, "path": "subDir"}
        fakeUploadResult = FilePart(
            filename=testTaskData["filename"], modified=testTaskData["utcModified"],
            size=testTaskData["size"], path=testTaskData["path"],
            fullPath=testTaskData["fullPath"], storingAccountID=fakeAccounts[0].id
        )
        fakeCloudAccount1 = MagicMock()
        fakeCloudAccount2 = MagicMock()
        cloudApiMock.side_effect = [fakeCloudAccount1, fakeCloudAccount2]

        testTask = Task(taskType=MessageTypes.UPLOAD_FILE, data=testTaskData, uuid=uuid4().hex)
        testHandler = UploadFileHandler(self.fakeDB)
        testHandler.setTask(testTask)

        testHandler.handle()

        self.assertEqual(fakeCloudAccount1.upload.call_count, 1)
        self.assertEqual(fakeCloudAccount1.upload.call_args[0][2], f"{testTaskData['filename']}__1__2.enc")
        self.assertEqual(fakeCloudAccount2.upload.call_count, 1)
        self.assertEqual(fakeCloudAccount2.upload.call_args[0][2], f"{testTaskData['filename']}__2__2.enc")

    @patch("control.cli.CONSOLE_ARGUMENTS", FakeGlobalConsoleArguments("testWorkspace"))
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch("os.unlink")
    @patch.object(CloudFilesCache, "getFile")
    @patch.object(CloudFilesCache, "insertFilePart")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch("control.message.open")
    def test_upload_is_interrupted_if_task_is_stale_and_no_response_is_sent(self, openMock, cloudApiMock, insertFilePartMock, getFileMock, os_unlinkMock, dispatchResponseMock):
        fakeFile = BytesIO(b"Lorem ipsum")
        openMock.return_value = fakeFile
        fakeAccounts = [AccountData(id=1, identifier="testAccountID", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken"})]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts
        getFileMock.return_value = None

        testTaskData = {"filename": "apple.txt", "size": 11, "fullPath": "subDir/apple.txt", "status": None, "utcModified": 10, "path": "subDir"}
        fakeUploadResult = None
        cloudApiMock.return_value.upload.return_value = fakeUploadResult

        testTask = Task(taskType=MessageTypes.UPLOAD_FILE, data=testTaskData, uuid=uuid4().hex, stale=True)
        testHandler = UploadFileHandler(self.fakeDB)
        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(openMock.call_count, 1)
        self.assertEqual(openMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")
        self.assertEqual(openMock.call_args[0][1], "rb")

        self.assertEqual(cloudApiMock.call_count, 0)

        self.assertEqual(insertFilePartMock.call_count, 0)

        self.assertEqual(getFileMock.call_count, 1)
        self.assertEqual(getFileMock.call_args[0][0], testTaskData["fullPath"])

        self.assertEqual(os_unlinkMock.call_count, 1)
        self.assertEqual(os_unlinkMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")

        self.assertEqual(dispatchResponseMock.call_count, 0)


class TestDownloadFileHandler(unittest.TestCase):

    @classmethod
    @patch("control.database.DatabaseAccess")
    def setUpClass(cls, fakeDB):
        cls.fakeDB = fakeDB

    @patch("control.cli.CONSOLE_ARGUMENTS", FakeGlobalConsoleArguments("testWorkspace"))
    @patch("os.rename")
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch.object(CloudFilesCache, "getFile")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch("control.message.open")
    def test_downloads_file_and_moves_it_to_client_workspace_and_sends_response(self, openMock, cloudApiMock, getFileMock, dispatchResponseMock, os_renameMock):
        openMock.return_value = BytesIO()
        testFileData = FileData(filename="apple.txt", modified=10, size=10, path="subDir", fullPath="subDir/apple.txt")
        testFilePart = FilePart(
            filename="apple.txt__1__1.enc", modified=10,
            size=testFileData.size + 16, path="subDir",
            fullPath="subDir/apple.txt__1__1.enc", storingAccountID=1
        )
        fakeAccounts = [
            AccountData(id=1, identifier="testAccountID1", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken1"}),
            AccountData(id=2, identifier="testAccountID2", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken2"})
        ]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts
        testCachedFileInfo = CachedFileData(data=testFileData, availablePartCount=1, totalPartCount=1, parts={"subDir/apple.txt__1__1.enc": testFilePart})
        getFileMock.return_value = testCachedFileInfo

        testTask = Task(taskType=MessageTypes.DOWNLOAD_FILE, data=testFileData.serialize(), uuid=uuid4().hex)

        testHandler = DownloadFileHandler(self.fakeDB)
        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(openMock.call_count, 1)
        self.assertEqual(openMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")
        self.assertEqual(openMock.call_args[0][1], "wb")

        self.assertEqual(cloudApiMock.call_count, 1)
        self.assertEqual(cloudApiMock.call_args[0][0], fakeAccounts[0])

        self.assertEqual(getFileMock.call_count, 1)
        self.assertEqual(getFileMock.call_args[0][0], testFileData.fullPath)

        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.FILE_STATUS_UPDATE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.uuid, testTask.uuid)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["filename"], testFileData.filename)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["path"], testFileData.path)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["fullPath"], testFileData.fullPath)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["modified"], testFileData.modified)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["size"], testFileData.size)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data["status"], FileStatuses.DOWNLOADING_TO_LOCAL)

        self.assertEqual(os_renameMock.call_count, 1)
        self.assertEqual(os_renameMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")
        self.assertEqual(os_renameMock.call_args[0][1], f"testWorkspace/client/{testTask.uuid}")

    @patch("control.cli.CONSOLE_ARGUMENTS", FakeGlobalConsoleArguments("testWorkspace"))
    @patch("os.remove")
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch.object(CloudFilesCache, "getFile")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch("control.message.open")
    def test_stops_download_and_does_not_send_response_and_cleans_up_if_file_download_is_interrupted(self, openMock, cloudApiMock, getFileMock, dispatchResponseMock, os_removeMock):
        openMock.return_value = BytesIO()
        testFileData = FileData(filename="apple.txt", modified=10, size=10, path="subDir", fullPath="subDir/apple.txt")
        testFilePart = FilePart(
            filename="apple.txt__1__1.enc", modified=10,
            size=testFileData.size + 16, path="subDir",
            fullPath="subDir/apple.txt__1__1.enc", storingAccountID=1
        )
        fakeAccounts = [
            AccountData(id=1, identifier="testAccountID1", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken1"}),
            AccountData(id=2, identifier="testAccountID2", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken2"})
        ]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts
        testCachedFileInfo = CachedFileData(data=testFileData, availablePartCount=1, totalPartCount=1, parts={"subDir/apple.txt__1__1.enc": testFilePart})
        getFileMock.return_value = testCachedFileInfo

        testTask = Task(taskType=MessageTypes.DOWNLOAD_FILE, data=testFileData.serialize(), uuid=uuid4().hex, stale=True)

        testHandler = DownloadFileHandler(self.fakeDB)
        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(openMock.call_count, 1)
        self.assertEqual(openMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")
        self.assertEqual(openMock.call_args[0][1], "wb")

        self.assertEqual(dispatchResponseMock.call_count, 0)

        self.assertEqual(os_removeMock.call_count, 1)
        self.assertEqual(os_removeMock.call_args[0][0], f"testWorkspace/server/{testTask.uuid}")


class TestDeleteFileHandler(unittest.TestCase):

    @classmethod
    @patch("control.database.DatabaseAccess")
    def setUpClass(cls, fakeDB):
        cls.fakeDB = fakeDB

    @patch.object(CloudFilesCache, "removeFile")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch.object(CloudFilesCache, "getFile")
    def test_delete_file_handler_removes_filedata_from_all_accounts(self, getFileMock, cloudApiMock, removeFileMock):
        testFileData = FileData(filename="apple.txt", modified=10, size=10, path="subDir", fullPath="subDir/apple.txt")
        testTask = Task(taskType=MessageTypes.DELETE_FILE, data={"fullPath": "apple.txt"})
        fakeAccounts = [
            AccountData(id=1, identifier="testAccountID1", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken1"}),
            AccountData(id=2, identifier="testAccountID2", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken2"})
        ]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts
        testFileParts = [
            FilePart(
                filename="apple.txt__1__2.enc", modified=10,
                size=21, path="subDir",
                fullPath="subDir/apple.txt__1__2.enc", storingAccountID=1
            ),
            FilePart(
                filename="apple.txt__2__2.enc", modified=10,
                size=21, path="subDir",
                fullPath="subDir/apple.txt__2__2.enc", storingAccountID=2
            )
        ]
        testCachedFileInfo = CachedFileData(data=testFileData, availablePartCount=2, totalPartCount=2, parts={filepart.filename: filepart for filepart in testFileParts})
        getFileMock.return_value = testCachedFileInfo

        fakeCloudAccount1 = MagicMock()
        fakeCloudAccount2 = MagicMock()
        cloudApiMock.side_effect = [fakeCloudAccount1, fakeCloudAccount2]

        testHandler = DeleteFileHandler(self.fakeDB)
        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(getFileMock.call_count, 1)
        self.assertEqual(getFileMock.call_args[0][0], testTask.data["fullPath"])

        self.assertEqual(cloudApiMock.call_count, 2)
        self.assertEqual(cloudApiMock.call_args_list[0][0][0], fakeAccounts[0])
        self.assertEqual(cloudApiMock.call_args_list[1][0][0], fakeAccounts[1])

        self.assertEqual(removeFileMock.call_count, 1)
        self.assertEqual(removeFileMock.call_args[0][0], testTask.data["fullPath"])

        self.assertEqual(fakeCloudAccount1.deleteFile.call_count, 1)
        self.assertEqual(fakeCloudAccount1.deleteFile.call_args[0][0], testFileParts[0])

        self.assertEqual(fakeCloudAccount2.deleteFile.call_count, 1)
        self.assertEqual(fakeCloudAccount2.deleteFile.call_args[0][0], testFileParts[1])


class TestMoveFileHandler(unittest.TestCase):

    @classmethod
    @patch("control.database.DatabaseAccess")
    def setUpClass(cls, fakeDB):
        cls.fakeDB = fakeDB

    @patch.object(CloudFilesCache, "moveFile")
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch.object(CloudFilesCache, "removeFile")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch.object(CloudFilesCache, "getFile")
    def test_removes_destination_path_on_all_accounts_then_moves_synced_files_and_sends_successful_response(self, getFileMock, cloudApiMock, removeFileMock, dispatchResponseMock, moveFileMock):
        testSourceFileData = FileData(filename="apple.txt", modified=10, size=10, path="", fullPath="apple.txt")
        testTargetFileData = FileData(filename="apple.txt", modified=10, size=20, path="subDir", fullPath="subDir/apple.txt")

        testTask = Task(taskType=MessageTypes.MOVE_FILE, data={"source": "apple.txt", "target": testTargetFileData.serialize()})
        fakeAccounts = [
            AccountData(id=1, identifier="testAccountID1", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken1"}),
            AccountData(id=2, identifier="testAccountID2", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken2"})
        ]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts

        testSourceFileParts = [
            FilePart(filename="apple.txt__1__2.enc", modified=10, size=21, path="", fullPath="apple.txt__1__2.enc", storingAccountID=1),
            FilePart(filename="apple.txt__2__2.enc", modified=10, size=21, path="", fullPath="apple.txt__2__2.enc", storingAccountID=2)
        ]
        testTargetFileParts = [
            FilePart(filename="apple.txt__1__2.enc", modified=15, size=26, path="subDir", fullPath="subDir/apple.txt__1__2.enc", storingAccountID=1),
            FilePart(filename="apple.txt__2__2.enc", modified=15, size=26, path="subDir", fullPath="subDir/apple.txt__2__2.enc", storingAccountID=2)
        ]

        testSourceCachedFileInfo = CachedFileData(data=testSourceFileData, availablePartCount=2, totalPartCount=2, parts={filepart.filename: filepart for filepart in testSourceFileParts})
        testTargetCachedFileInfo = CachedFileData(data=testTargetFileData, availablePartCount=2, totalPartCount=2, parts={filepart.filename: filepart for filepart in testTargetFileParts})
        getFileMock.side_effect = [testTargetCachedFileInfo, testSourceCachedFileInfo]

        fakeCloudAccount1 = MagicMock()
        fakeCloudAccount1.accountData = fakeAccounts[0]
        fakeCloudAccount2 = MagicMock()
        fakeCloudAccount2.accountData = fakeAccounts[1]
        cloudApiMock.side_effect = [fakeCloudAccount1, fakeCloudAccount2, fakeCloudAccount1, fakeCloudAccount2]

        testHandler = MoveFileHandler(self.fakeDB)
        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(fakeCloudAccount1.deleteFile.call_count, 1)
        self.assertEqual(fakeCloudAccount2.deleteFile.call_count, 1)
        self.assertEqual(fakeCloudAccount1.moveFile.call_count, 1)
        self.assertEqual(fakeCloudAccount2.moveFile.call_count, 1)
        self.assertEqual(getFileMock.call_count, 2)
        self.assertEqual(removeFileMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(moveFileMock.call_count, 1)

        self.assertEqual(fakeCloudAccount1.deleteFile.call_args[0][0], testTargetFileParts[0])
        self.assertEqual(fakeCloudAccount2.deleteFile.call_args[0][0], testTargetFileParts[1])
        self.assertEqual(fakeCloudAccount1.moveFile.call_args[0][0], testSourceFileParts[0])
        self.assertEqual(fakeCloudAccount1.moveFile.call_args[0][1], testTargetFileParts[0].fullPath)
        self.assertEqual(fakeCloudAccount2.moveFile.call_args[0][0], testSourceFileParts[1])
        self.assertEqual(fakeCloudAccount2.moveFile.call_args[0][1], testTargetFileParts[1].fullPath)

        self.assertEqual(getFileMock.call_args_list[0][0][0], testTargetFileData.fullPath)
        self.assertEqual(getFileMock.call_args_list[0][0][0], testSourceFileData.fullPath)
        self.assertEqual(removeFileMock.call_args[0][0], testTargetFileData.fullPath)

        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data, {"moveSuccessful": True, "from": "apple.txt", "to": testTargetFileData.fullPath})
        self.assertEqual(moveFileMock.call_args[0][0], "apple.txt")
        self.assertEqual(moveFileMock.call_args[0][1], "subDir/apple.txt")

    @patch.object(CloudFilesCache, "moveFile")
    @patch.object(MessageDispatcher, "dispatchResponse")
    @patch.object(CloudFilesCache, "removeFile")
    @patch.object(CloudAPIFactory, "fromAccountData")
    @patch.object(CloudFilesCache, "getFile")
    def test_removes_destination_path_on_all_accounts_then_tries_to_move_unsynced_files_and_sends_unsuccessful_response(self, getFileMock, cloudApiMock, removeFileMock, dispatchResponseMock, moveFileMock):
        testSourceFileData = FileData(filename="apple.txt", modified=10, size=10, path="", fullPath="apple.txt")
        testTargetFileData = FileData(filename="apple.txt", modified=10, size=20, path="subDir", fullPath="subDir/apple.txt")

        testTask = Task(taskType=MessageTypes.MOVE_FILE, data={"source": "apple.txt", "target": testTargetFileData.serialize()})
        fakeAccounts = [
            AccountData(id=1, identifier="testAccountID1", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken1"}),
            AccountData(id=2, identifier="testAccountID2", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken2"})
        ]
        self.fakeDB.getAllAccounts.return_value = fakeAccounts

        testSourceFileParts = [
            FilePart(filename="apple.txt__1__2.enc", modified=10, size=21, path="", fullPath="apple.txt__1__2.enc", storingAccountID=1),
        ]
        testTargetFileParts = [
            FilePart(filename="apple.txt__1__2.enc", modified=15, size=26, path="subDir", fullPath="subDir/apple.txt__1__2.enc", storingAccountID=1),
            FilePart(filename="apple.txt__2__2.enc", modified=15, size=26, path="subDir", fullPath="subDir/apple.txt__2__2.enc", storingAccountID=2)
        ]

        testSourceCachedFileInfo = CachedFileData(data=testSourceFileData, availablePartCount=1, totalPartCount=2, parts={filepart.filename: filepart for filepart in testSourceFileParts})
        testTargetCachedFileInfo = CachedFileData(data=testTargetFileData, availablePartCount=2, totalPartCount=2, parts={filepart.filename: filepart for filepart in testTargetFileParts})
        getFileMock.side_effect = [testTargetCachedFileInfo, testSourceCachedFileInfo]

        fakeCloudAccount1 = MagicMock()
        fakeCloudAccount1.accountData = fakeAccounts[0]
        fakeCloudAccount2 = MagicMock()
        fakeCloudAccount2.accountData = fakeAccounts[1]
        cloudApiMock.side_effect = [fakeCloudAccount1, fakeCloudAccount2, fakeCloudAccount1, fakeCloudAccount2]

        testHandler = MoveFileHandler(self.fakeDB)
        testHandler.setTask(testTask)
        testHandler.handle()

        self.assertEqual(fakeCloudAccount1.deleteFile.call_count, 2)
        self.assertEqual(fakeCloudAccount2.deleteFile.call_count, 1)
        self.assertEqual(fakeCloudAccount1.moveFile.call_count, 0)
        self.assertEqual(fakeCloudAccount2.moveFile.call_count, 0)
        self.assertEqual(getFileMock.call_count, 2)
        self.assertEqual(removeFileMock.call_count, 2)
        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(moveFileMock.call_count, 0)

        self.assertEqual(fakeCloudAccount1.deleteFile.call_args[0][0], testSourceFileParts[0])
        self.assertEqual(fakeCloudAccount2.deleteFile.call_args[0][0], testTargetFileParts[1])

        self.assertEqual(getFileMock.call_args_list[0][0][0], testTargetFileData.fullPath)
        self.assertEqual(removeFileMock.call_args[0][0], testSourceFileData.fullPath)

        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].data, {"moveSuccessful": False, "from": "apple.txt", "to": testTargetFileData.fullPath})
