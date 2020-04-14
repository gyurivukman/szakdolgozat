import re
import logging
from datetime import datetime, timedelta

import paramiko
import dropbox

from Crypto.Cipher import AES

from model.account import AccountTypes, AccountData
from model.file import FileData
from model.task import Task

from control.util import chunkSizeGenerator

moduleLogger = logging.getLogger(__name__)


class CloudAPIWrapper:

    def __init__(self, accountData):
        self.accountData = accountData
        self._task = None
        self._logger = self._getLogger()

    def upload(self, fileHandle, toUploadSize, partName, task):
        raise NotImplementedError("Derived class must implement method 'upload'!")

    def download(self, fileHandle, remotePath, task):
        raise NotImplementedError("Derived class must implement method 'download'!")

    def getFileList(self):
        raise NotImplementedError("Derived class must implement method 'getFileList'!")

    def delete(self):
        raise NotImplementedError("Derived class must implement method 'delete'!")

    def move(self, oldPath, newPath):
        raise NotImplementedError("Derived class must implement method 'move'!")

    def _getLogger(self):
        raise NotImplementedError("Derived class must implement method '_getLogger'!")


class DropboxAccountWrapper(CloudAPIWrapper):

    def __init__(self, *args):
        super().__init__(*args)
        self.__dbx = dropbox.Dropbox(self.accountData.data['apiToken'])
        self.__UPLOAD_CHUNK_SIZE = 1048576

    def getFileList(self):
        files = []
        result = self.__dbx.files_list_folder("", recursive=True)
        files = [self.__toFileData(entry) for entry in result.entries if type(entry) == (dropbox.files.FileMetadata) and entry.name[-4:] == ".enc" and entry.size > 0]

        return files

    def upload(self, fileHandle, toUploadSize, partName, task):
        self._logger.debug(f"Uploading filePart: {partName}")

        cipher = AES.new(self.accountData.cryptoKey.encode(), AES.MODE_CFB)

        if not task.stale:
            upload_session_start_result = self.__dbx.files_upload_session_start(
                cipher.iv
            )

            offset = len(cipher.iv)
            cursor = dropbox.files.UploadSessionCursor(
                session_id=upload_session_start_result.session_id,
                offset=offset,
            )
            rawOffset = task.data['userTimezone']
            timeZoneOffset = timedelta(hours=int(rawOffset[1:3]), minutes=int(rawOffset[3:]))

            clientModified = datetime.utcfromtimestamp(task.data['utcModified']) + timeZoneOffset if rawOffset[0] == "+" else datetime.utcfromtimestamp(task.data['utcModified']) - timeZoneOffset
            remotePath = f"{task.data['path']}/{partName}"

            commit = dropbox.files.CommitInfo(path=f"{remotePath}", mode=dropbox.files.WriteMode.overwrite, client_modified=clientModified)

            for chunkSize, remaining in chunkSizeGenerator(toUploadSize, self.__UPLOAD_CHUNK_SIZE):
                if not task.stale:
                    data = cipher.encrypt(fileHandle.read(chunkSize))
                    if remaining == 0:
                        print(
                            self.__dbx.files_upload_session_finish(
                                data, cursor, commit
                            )
                        )
                    else:
                        self.__dbx.files_upload_session_append(
                            data,
                            cursor.session_id,
                            cursor.offset,
                        )
                    cursor.offset += chunkSize

    def _getLogger(self):
        return moduleLogger.getChild("DropboxAccountWrapper")

    def __toFileData(self, entry):
        print(entry.client_modified.tzinfo)
        return FileData(
            filename=entry.name,
            modified=int(entry.client_modified.timestamp()),
            size=entry.size - 16,
            path=entry.path_display.replace(f"/{entry.name}", "").lstrip("/"),
            fullPath=entry.path_display.lstrip("/")
        )


class SFTPCloudAccount(CloudAPIWrapper):  # TODO Stretchgoal!

    def __init__(self, *args):
        super().__init__(*args)

        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__client.connect("localhost", 22, self.accountData.data['username'], self.accountData.data['password'])

        self.__sftp = self.__client.open_sftp()

    def getFileList(self):
        stdin, stdout, stderr = self.__client.exec_command("find remoteStorage/ -type f -name \*.enc -printf '%T@ %s %P %p\n'")

        fileList = []

        for line in stdout:
            splitted = line.split(" ")
            modified = int(float(splitted[0]))
            size = int(splitted[1])
            filename = splitted[2].split("/")[-1]
            fullPath = splitted[3][:-1].replace("remoteStorage/", "")
            path = fullPath.replace(f"{filename}", "").rstrip("/")

            fileList.append(FileData(filename, modified, size, path, fullPath))

        return fileList

    def __del__(self):
        self.__sftp.close()
        self.__client.close()


class CloudAPIFactory:
    __typeToClassMap = {
        AccountTypes.Dropbox: DropboxAccountWrapper,
        AccountTypes.GoogleDrive: None  # TODO
    }

    @staticmethod
    def fromAccountData(accountData):
        return CloudAPIFactory.__typeToClassMap[accountData.accountType](accountData)
