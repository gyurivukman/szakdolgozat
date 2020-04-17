# TODO nem kell, csak mentés.
import os
import datetime
import sys
from uuid import uuid4
from io import IOBase, BufferedReader, BufferedWriter

import googleapiclient

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

from Crypto.Cipher import AES


class InterruptibleGoogleDriveUploadFileHandle(BufferedReader):

    def __init__(self, handle):
        self.__cipher = AES.new(b"Sixteen Byte Key", AES.MODE_CFB)
        super().__init__(handle)
        self.seek(0, os.SEEK_END)
        self.__progressSize = self.tell()
        self.seek(0, 0)

    def read(self, chunkSize):
        # print(f"Reading {(self.tell()/self.__progressSize) * 100}%")
        data = super().read(chunkSize)
        return self.__cipher.encrypt(data)


class InterruptibleGoogleDriveDownloadFileHandle(BufferedWriter):

    def __init__(self, handle):
        self.__cipher = None
        super().__init__(handle)

    def write(self, data):
        if self.tell() == 0:
            self.__cipher = AES.new(b"Sixteen Byte Key", AES.MODE_CFB, iv=data[0:16])
            super().write(self.__cipher.decrypt(data[16:]))
        else:
            super().write(self.__cipher.decrypt(data))


credentials = service_account.Credentials.from_service_account_file(
    "cred.json",
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build('drive', 'v3', credentials=credentials)


def search():
    results = service.files().list(
        q="'root' in parents and name contains '.enc'",
        fields="nextPageToken, files(id, name, modifiedTime, size)"
    ).execute()
    items = results.get('files', [])  # TODO Kell enc szűrő
    print("\n")
    for item in items:
        print(item)
    print("\n")


def upload(path):
    stats = os.stat(path)
    rawModifiedTime = stats.st_mtime
    modified = datetime.datetime.utcfromtimestamp(int(rawModifiedTime))

    metadata = {"name": f"{path}__1__1.enc", "parents": ["root"], "mimeType": "application/octet-stream", "modifiedTime": modified.strftime("%Y-%m-%dT%H:%M:%SZ")}

    tmpFileName = uuid4().hex
    cipher = AES.new(b"Sogron1990052000", AES.MODE_CFB)

    with open(tmpFileName, "wb") as outputFile:
        with open(path, "rb") as inputFile:
            outputFile.write(cipher.iv)
            data = inputFile.read(512000)
            while data:
                encrypted = cipher.encrypt(data)
                outputFile.write(data)
                data = inputFile.read(512000)

    with open(tmpFileName, "rb") as rawHandle:
        handle = InterruptibleGoogleDriveUploadFileHandle(rawHandle)
        media = MediaIoBaseUpload(handle, mimetype="application/octet-stream", resumable=True, chunksize=1024000)

        # media = MediaIoBaseUpload(rawFileHandle, mimetype="application/octet-stream", resumable=True, chunksize=1024000)
        res = service.files().create(body=metadata, media_body=media).execute()
        print(res)

    os.unlink(tmpFileName)


def cleanup(path):
    res = service.files().delete(fileId=path).execute()
    print(res)

    # print(dir(service.files()))


def download(fileID, name):  # 11Ps6SIQ9ej7qa6GpfcEaHaBOUPqshfH7

    with open(name, "wb") as rawFileHandle:
        handle = InterruptibleGoogleDriveDownloadFileHandle(rawFileHandle)
        request = service.files().get_media(fileId=fileID)
        downloader = MediaIoBaseDownload(handle, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        # request = service.files().create(body=metadata, media_body=media).execute()
        # media = MediaIoBaseDownload(handle, fileId="1i9Z2TvOlulOuAABCCXaAfDfUJmJ66GHQ", resumable=True, chunksize=262144)
        # print(res)


if __name__ == "__main__":
    task = sys.argv[1][1]

    if task == "u":
        path = sys.argv[2]
        upload(path)
    if task == "d":
        download(sys.argv[2], sys.argv[3])
    elif task == "f":
        search()
    elif task == "c":
        path = sys.argv[2]
        cleanup(path)
