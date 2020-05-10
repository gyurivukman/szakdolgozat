import unittest
import warnings
import datetime

from unittest.mock import patch, MagicMock
from io import BytesIO

from control.account import DropboxAccountWrapper
from model.account import AccountTypes, AccountData
from model.task import Task
from model.message import MessageTypes
from model.file import FilePart

from dropbox.files import FileMetadata
from Crypto.Cipher import AES

warnings.filterwarnings("ignore", category=DeprecationWarning)


class TestDropboxAccountWrapper(unittest.TestCase):

    def setUp(self):
        self.testAccountData = AccountData(
            AccountTypes.Dropbox,
            "testIdentifier",
            "sixteen byte key",
            {"apiToken": "testApiToken"},
            1
        )

    @patch("dropbox.Dropbox")
    def test_getFileList_returns_encrypted_files_recursively(self, mockDropbox):
        testCloudFiles = [
            FileMetadata(name="apple.txt__1__1.enc", size=5, client_modified=datetime.datetime(2020, 1, 1, 6, 10, 15), path_display="/apple.txt__1__1.enc"),
            FileMetadata(name="pear.txt__1__2.enc", size=10, client_modified=datetime.datetime(2020, 1, 1, 7, 10, 15), path_display="/subDir/pear.txt__1__2.enc"),
            FileMetadata(name="notAnEncodedFile.jpeg", size=20, client_modified=datetime.datetime(2020, 1, 1, 7, 10, 15), path_display="/notAnEncodedFile.jpeg")
        ]
        mockDropbox.return_value.files_list_folder.return_value.entries = testCloudFiles
        cloudAccount = DropboxAccountWrapper(self.testAccountData)
        files = cloudAccount.getFileList()

        self.assertEqual(len(files), 2)
        self.assertEqual(mockDropbox.return_value.files_list_folder.call_args[0][0], "")
        self.assertEqual(mockDropbox.return_value.files_list_folder.call_args[1], {"recursive": True})

        self.assertEqual(files[0].filename, testCloudFiles[0].name)
        self.assertEqual(files[0].modified, int(testCloudFiles[0].client_modified.timestamp()))
        self.assertEqual(files[0].size, testCloudFiles[0].size)
        self.assertEqual(files[0].path, "")
        self.assertEqual(files[0].fullPath, "apple.txt__1__1.enc")
        self.assertEqual(files[0].storingAccountID, self.testAccountData.id)

        self.assertEqual(files[1].filename, testCloudFiles[1].name)
        self.assertEqual(files[1].modified, int(testCloudFiles[1].client_modified.timestamp()))
        self.assertEqual(files[1].size, testCloudFiles[1].size)
        self.assertEqual(files[1].path, "subDir")
        self.assertEqual(files[1].fullPath, "subDir/pear.txt__1__2.enc")
        self.assertEqual(files[1].storingAccountID, self.testAccountData.id)

    @patch("dropbox.files.UploadSessionCursor")
    @patch("dropbox.Dropbox")
    def test_upload_writes_iv_and_encrypts_file_data(self, mockDropbox, mockUploadCursor):
        uploadSessionStarter = MagicMock()
        uploadSessionAppender = MagicMock()

        mockDropbox.return_value.files_upload_session_start = uploadSessionStarter
        mockDropbox.return_value.files_upload_session_finish = uploadSessionAppender

        testSecretData = b"secret test data"
        testFileHandle = BytesIO(testSecretData)
        testPartName = "testFile__1__1.enc"
        testClientModified = datetime.datetime(2020, 1, 1, 10, 5, 30)

        testFileData = {"userTimezone": "+0200", "utcModified": testClientModified.timestamp(), "path": "subDir"}
        testTask = Task(taskType=MessageTypes.UPLOAD_FILE, data=testFileData)

        cloudAccount = DropboxAccountWrapper(self.testAccountData)
        result = cloudAccount.upload(testFileHandle, len(testSecretData), testPartName, testTask)

        cipher = AES.new(self.testAccountData.cryptoKey.encode(), AES.MODE_CFB, iv=uploadSessionStarter.call_args[0][0])
        encoded = mockDropbox.return_value.files_upload_session_finish.call_args[0][0]

        self.assertNotEqual(encoded, testSecretData)
        self.assertEqual(cipher.decrypt(encoded), testSecretData)

    @patch("requests.get")
    def test_download(self, mockRequest):
        secretData = b"secret test data"
        testEncoder = AES.new(self.testAccountData.cryptoKey.encode(), AES.MODE_CFB)
        testIV = testEncoder.iv

        ivResponse = MagicMock()
        ivResponse.content = testIV

        encryptedDataResponse = MagicMock()
        encryptedDataResponse.content = testEncoder.encrypt(secretData)

        mockRequest.side_effect = [ivResponse, encryptedDataResponse]

        testDownloadFileHandle = BytesIO()
        testFilePartInfo = FilePart(
            filename="apple.txt__1__1.enc", modified=int(datetime.datetime(2020, 1, 1, 10, 10, 30).timestamp()),
            size=len(encryptedDataResponse.content) + len(testIV), path="", fullPath="apple.txt__1__1.enc",
            storingAccountID=self.testAccountData.id, extraInfo={}
        )

        testDownloadFileTask = Task(taskType=MessageTypes.DOWNLOAD_FILE)
        cloudAccount = DropboxAccountWrapper(self.testAccountData)
        cloudAccount.download(testDownloadFileHandle, testFilePartInfo, testDownloadFileTask)

        testDownloadFileHandle.seek(0)

        self.assertEqual(secretData, testDownloadFileHandle.read())


if __name__ == '__main__':
    unittest.main()
