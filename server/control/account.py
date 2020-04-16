import re
import logging
import json
import time

from uuid import uuid4
from os import unlink

from io import BufferedReader, BufferedWriter
from datetime import datetime, timedelta, timezone

import paramiko
import dropbox
import requests
import googleapiclient

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

from Crypto.Cipher import AES

from model.account import AccountTypes, AccountData
from model.file import FileData
from model.task import Task

from control.util import chunkSizeGenerator, httpRangeHeaderIntervalGenerator

moduleLogger = logging.getLogger(__name__)


class CloudAPIWrapper:

    def __init__(self, accountData):
        self.accountData = accountData
        self._task = None
        self._logger = self._getLogger()

    def upload(self, fileHandle, toUploadSize, partName, task):
        raise NotImplementedError("Derived class must implement method 'upload'!")

    def download(self, fileHandle, cachedFileInfo, partInfo, task):
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
        self.__DOWNLOAD_URL = "https://content.dropboxapi.com/2/files/download"
        self.__UPLOAD_CHUNK_SIZE = 1048576
        self.__DOWNLOAD_CHUNK_SIZE = 1048576

    def __toFileData(self, entry):
        return FileData(
            filename=entry.name,
            modified=int(entry.client_modified.timestamp()),
            size=entry.size,
            path=entry.path_display.replace(f"/{entry.name}", "").lstrip("/"),
            fullPath=entry.path_display.lstrip("/")
        )

    def __sendDownloadCompleteResponse(self):
        data = self._task.subject

    def _getLogger(self):
        return moduleLogger.getChild("DropboxAccountWrapper")

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

    def download(self, fileHandle, cachedFileInfo, partInfo, task):
        token = self.accountData.data["apiToken"]
        remotePath = f"{cachedFileInfo.data.fullPath.replace(cachedFileInfo.data.filename, '')}{partInfo.partName}"

        headers = {"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": f"/{remotePath}"}), "Range": "bytes=0-15"}
        res = requests.get(self.__DOWNLOAD_URL, headers=headers)
        cipher = AES.new(self.accountData.cryptoKey.encode(), AES.MODE_CFB, iv=res.content)

        for interval in httpRangeHeaderIntervalGenerator(partInfo.size, self.__DOWNLOAD_CHUNK_SIZE):
            if not task.stale:
                headers["Range"] = f"bytes={interval[0]}-{interval[1]}"

                res = requests.get(self.__DOWNLOAD_URL, headers=headers)
                decrypted = cipher.decrypt(res.content)
                fileHandle.write(decrypted)


class TaskInterruptedException(Exception):
    pass


class InterruptibleGoogleDriveUploadFileHandle(BufferedReader):

    def __init__(self, handle):
        super().__init__(handle)

    def close(self):
        pass


class InterruptibleGoogleDriveDownloadFileHandle(BufferedWriter):

    def __init__(self, handle, aesKey):
        self.__cipher = None
        self.__aesKey = aesKey
        super().__init__(handle)

    def write(self, data):
        if not self.__cipher:
            self.__cipher = AES.new(self.__aesKey.encode(), AES.MODE_CFB, iv=data[0:16])
            super().write(self.__cipher.decrypt(data[16:]))
        else:
            super().write(self.__cipher.decrypt(data))

    def close(self):
        pass


class GoogleDriveAccountWrapper(CloudAPIWrapper):

    def __init__(self, *args):
        super().__init__(*args)

        self.__UPLOAD_CHUNK_SIZE = 1048576
        self.__DOWNLOAD_CHUNK_SIZE = 1048576

        parsedCreds = json.loads(json.dumps(self.accountData.data))

        credentials = service_account.Credentials.from_service_account_info(parsedCreds, scopes=["https://www.googleapis.com/auth/drive"])
        self.__service = build('drive', 'v3', credentials=credentials)

    def getFileList(self):
        files = []
        hasMore = True
        results = self.__service.files().list(
            q="'root' in parents and name contains '.enc'",
            fields="nextPageToken, files(id, name, modifiedTime, size)"
        ).execute()

        while hasMore:
            currentBatch = [self.__toFileData(entry) for entry in results.get("files", [])]
            files.extend(currentBatch)
            nextPageToken = results.get("nextPageToken", None)
            hasMore = nextPageToken is not None
            if hasMore:
                results = self.__service.files().list(
                    q="'root' in parents and name contains '.enc'",
                    fields="nextPageToken, files(id, name, modifiedTime, size)",
                    pageToken=nextPageToken
                ).execute()

        return files

    def _getLogger(self):
        return moduleLogger.getChild("GoogleDriveAccountWrapper")

    def __toFileData(self, entry):
        fileName = entry["name"].split("/")[-1]
        path = entry["name"].replace(fileName, "")
        fullPath = entry["name"]

        unawareModifiedTime = time.strptime(entry["modifiedTime"], "%Y-%m-%dT%H:%M:%S.000Z")
        modifiedTime = datetime(*unawareModifiedTime[:6], tzinfo=timezone.utc)

        return FileData(
            filename=fileName,
            modified=int(modifiedTime.timestamp()),
            size=int(entry["size"]),
            path=path,
            fullPath=fullPath,
            extraInfo={"id": entry["id"]}
        )

    def download(self, fileHandle, cachedFileInfo, partInfo, task):
        self._logger.debug(f"Downloading: {partInfo}")

        handle = InterruptibleGoogleDriveDownloadFileHandle(fileHandle, self.accountData.cryptoKey)
        request = self.__service.files().get_media(fileId=partInfo.extraInfo["id"])
        downloader = MediaIoBaseDownload(handle, request, chunksize=self.__DOWNLOAD_CHUNK_SIZE)

        done = False
        while not done:
            status, done = downloader.next_chunk()

    def upload(self, fileHandle, toUploadSize, partName, task):
        timeModified = datetime.utcfromtimestamp(task.data['utcModified'])
        uploadName = task.data["fullPath"].replace(task.data["filename"], partName)

        metadata = {"name": f"{uploadName}", "parents": ["root"], "mimeType": "application/octet-stream", "modifiedTime": timeModified.strftime("%Y-%m-%dT%H:%M:%SZ")}

        tmpFileName = uuid4().hex
        cipher = AES.new(self.accountData.cryptoKey.encode(), AES.MODE_CFB)

        with open(tmpFileName, "wb") as outputFile:
            outputFile.write(cipher.iv)
            for chunk, remainder in chunkSizeGenerator(toUploadSize, self.__UPLOAD_CHUNK_SIZE):
                data = fileHandle.read(chunk)
                encrypted = cipher.encrypt(data)
                outputFile.write(encrypted)

        with open(tmpFileName, "rb") as rawHandle:
            interruptibleHandle = InterruptibleGoogleDriveUploadFileHandle(rawHandle)
            try:
                media = MediaIoBaseUpload(interruptibleHandle, mimetype="application/octet-stream", resumable=True, chunksize=self.__UPLOAD_CHUNK_SIZE)
                res = self.__service.files().create(body=metadata, media_body=media, fields="id, name, modifiedTime, size").execute()
                self._logger.debug(res)
            except TaskInterruptedException as e:
                self._logger.info("Google drive upload interrupted, aborting and cleaning up..")
        unlink(tmpFileName)


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
        AccountTypes.GoogleDrive: GoogleDriveAccountWrapper
    }

    @staticmethod
    def fromAccountData(accountData):
        return CloudAPIFactory.__typeToClassMap[accountData.accountType](accountData)
