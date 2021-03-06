import re
import logging
import json
import time
from uuid import uuid4
from os import unlink
from io import BufferedReader, BufferedWriter
from datetime import datetime, timedelta, timezone

import dropbox
import requests
import googleapiclient
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from Crypto.Cipher import AES

import control.cli
from model.account import AccountTypes, AccountData
from model.file import FileData, FilePart
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

    def download(self, fileHandle, partInfo, task):
        raise NotImplementedError("Derived class must implement method 'download'!")

    def getFileList(self):
        raise NotImplementedError("Derived class must implement method 'getFileList'!")

    def deleteFile(self, partInfo):
        raise NotImplementedError("Derived class must implement method 'delete'!")

    def moveFile(self, partInfo, targetFullPath):
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

    def getFileList(self):
        files = []
        result = self.__dbx.files_list_folder("", recursive=True)
        files = [self.__toFilePart(entry) for entry in result.entries if type(entry) == (dropbox.files.FileMetadata) and entry.name[-4:] == ".enc" and entry.size > 0]

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
            remotePath = f"/{task.data['path']}/{partName}" if len(task.data['path']) > 0 else f"/{partName}"

            commit = dropbox.files.CommitInfo(path=f"{remotePath}", mode=dropbox.files.WriteMode.overwrite, client_modified=clientModified)
            uploadResult = None

            for chunkSize, remaining in chunkSizeGenerator(toUploadSize, self.__UPLOAD_CHUNK_SIZE):
                if not task.stale:
                    data = cipher.encrypt(fileHandle.read(chunkSize))
                    if remaining == 0:
                        result = self.__dbx.files_upload_session_finish(data, cursor, commit)
                        uploadResult = self.__toFilePart(result)
                    else:
                        self.__dbx.files_upload_session_append(
                            data,
                            cursor.session_id,
                            cursor.offset,
                        )
                    cursor.offset += chunkSize
            return uploadResult

    def download(self, fileHandle, partInfo, task):
        token = self.accountData.data["apiToken"]

        headers = {"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": f"/{partInfo.fullPath}"}), "Range": "bytes=0-15"}
        res = requests.get(self.__DOWNLOAD_URL, headers=headers)
        cipher = AES.new(self.accountData.cryptoKey.encode(), AES.MODE_CFB, iv=res.content)

        for interval in httpRangeHeaderIntervalGenerator(partInfo.size, self.__DOWNLOAD_CHUNK_SIZE):
            if task.stale:
                self._logger.info("Dropbox download interrupted.")
                break
            else:
                headers["Range"] = f"bytes={interval[0]}-{interval[1]}"

                res = requests.get(self.__DOWNLOAD_URL, headers=headers)
                decrypted = cipher.decrypt(res.content)
                fileHandle.write(decrypted)

    def deleteFile(self, partInfo):
        self.__dbx.files_delete(f"/{partInfo.fullPath}")

    def moveFile(self, partInfo, targetFullPath):
        sourcePath = f"/{partInfo.fullPath}"
        destinationPath = f"/{targetFullPath}"

        self._logger.debug(self.__dbx.files_move(sourcePath, destinationPath))

    def __toFilePart(self, entry):
        return FilePart(
            filename=entry.name,
            modified=int(entry.client_modified.timestamp()),
            size=entry.size,
            path=entry.path_display.replace(f"/{entry.name}", "").lstrip("/"),
            fullPath=entry.path_display.lstrip("/"),
            storingAccountID=self.accountData.id
        )

    def _getLogger(self):
        return moduleLogger.getChild("DropboxAccountWrapper")


class TaskInterruptedException(Exception):
    pass


class InterruptibleGoogleDriveUploadFileHandle(BufferedReader):

    def __init__(self, handle, task):
        super().__init__(handle)
        self.__task = task

    def read(self, chunk):
        if not self.__task.stale:
            return super().read(chunk)
        else:
            raise TaskInterruptedException("")

    def close(self):
        pass


class InterruptibleGoogleDriveDownloadFileHandle(BufferedWriter):

    def __init__(self, handle, aesKey, task):
        self.__cipher = None
        self.__aesKey = aesKey
        self.__task = task
        super().__init__(handle)

    def write(self, data):
        if not self.__task.stale:
            if not self.__cipher:
                self.__cipher = AES.new(self.__aesKey.encode(), AES.MODE_CFB, iv=data[0:16])
                super().write(self.__cipher.decrypt(data[16:]))
                super().flush()
            else:
                super().write(self.__cipher.decrypt(data))
                super().flush()
        else:
            raise TaskInterruptedException("")

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
            currentBatch = [self.__toFilePart(entry) for entry in results.get("files", [])]
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

    def download(self, fileHandle, partInfo, task):
        self._logger.debug(f"Downloading: {partInfo}")
        try:
            handle = InterruptibleGoogleDriveDownloadFileHandle(fileHandle, self.accountData.cryptoKey, task)
            request = self.__service.files().get_media(fileId=partInfo.extraInfo["id"])
            downloader = MediaIoBaseDownload(handle, request, chunksize=self.__DOWNLOAD_CHUNK_SIZE)

            done = False
            while not done:
                status, done = downloader.next_chunk()
        except TaskInterruptedException:
            self._logger.info("Google drive download interrupted.")

    def upload(self, fileHandle, toUploadSize, partName, task):
        self._logger.debug("Uploading to Google Drive.")
        timeModified = datetime.utcfromtimestamp(task.data['utcModified'])
        uploadName = task.data["fullPath"].replace(task.data["filename"], partName)

        metadata = {"name": f"{uploadName}", "parents": ["root"], "mimeType": "application/octet-stream", "modifiedTime": timeModified.strftime("%Y-%m-%dT%H:%M:%SZ")}

        tmpFile = f"{control.cli.CONSOLE_ARGUMENTS.workspace}/server/{uuid4().hex}"
        cipher = AES.new(self.accountData.cryptoKey.encode(), AES.MODE_CFB)
        if not task.stale:
            with open(tmpFile, "wb") as outputFile:
                outputFile.write(cipher.iv)
                for chunk, remainder in chunkSizeGenerator(toUploadSize, self.__UPLOAD_CHUNK_SIZE):
                    if task.stale:
                        self._logger.info("Dropbox upload interrupted")
                        break
                    else:
                        data = fileHandle.read(chunk)
                        encrypted = cipher.encrypt(data)
                        outputFile.write(encrypted)
        if task.stale:
            self._logger.info("Google drive upload interrupted, aborting and cleaning up..")
            unlink(tmpFile)
        else:
            with open(tmpFile, "rb") as rawHandle:
                interruptibleHandle = InterruptibleGoogleDriveUploadFileHandle(rawHandle, task)
                try:
                    media = MediaIoBaseUpload(interruptibleHandle, mimetype="application/octet-stream", resumable=True, chunksize=self.__UPLOAD_CHUNK_SIZE)
                    res = self.__service.files().create(body=metadata, media_body=media, fields="id, name, modifiedTime, size").execute()
                    self._logger.debug(f"Finishing google drive upload {res}")
                    unlink(tmpFile)
                    return self.__toFilePart(res)
                except TaskInterruptedException:
                    self._logger.info("Google drive upload cancelled, aborting and cleaning up..")
                    unlink(tmpFile)

    def moveFile(self, partInfo, targetFullPath):
        timeModified = datetime.utcfromtimestamp(partInfo.modified)
        metadata = {"name": f"{targetFullPath}", "modifiedTime": timeModified.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.__service.files().update(fileId=partInfo.extraInfo["id"], body=metadata).execute()

    def deleteFile(self, partInfo):
        self.__service.files().delete(fileId=partInfo.extraInfo["id"]).execute()

    def _getLogger(self):
        return moduleLogger.getChild("GoogleDriveAccountWrapper")

    def __toFilePart(self, entry):
        filename = entry["name"].split("/")[-1]
        path = entry["name"].replace(filename, "").rstrip("/")
        fullPath = entry["name"]

        unawareModifiedTime = time.strptime(entry["modifiedTime"], "%Y-%m-%dT%H:%M:%S.000Z")
        modifiedTime = datetime(*unawareModifiedTime[:6], tzinfo=timezone.utc)

        filePart = FilePart(
            filename=filename,
            modified=int(modifiedTime.timestamp()),
            size=int(entry["size"]),
            path=path,
            fullPath=fullPath,
            storingAccountID=self.accountData.id,
            extraInfo={"id": entry["id"]}
        )
        return filePart

    def __createTemporaryEncryptedUploadFile(self):
        with open(tmpFile, "wb") as outputFile:
            outputFile.write(cipher.iv)
            for chunk, remainder in chunkSizeGenerator(toUploadSize, self.__UPLOAD_CHUNK_SIZE):
                data = fileHandle.read(chunk)
                encrypted = cipher.encrypt(data)
                outputFile.write(encrypted)


class CloudAPIFactory:
    __typeToClassMap = {
        AccountTypes.Dropbox: DropboxAccountWrapper,
        AccountTypes.GoogleDrive: GoogleDriveAccountWrapper
    }

    @staticmethod
    def fromAccountData(accountData):
        return CloudAPIFactory.__typeToClassMap[accountData.accountType](accountData)
