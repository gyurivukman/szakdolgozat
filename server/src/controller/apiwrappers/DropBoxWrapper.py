import sys
import datetime
import time
import dropbox
import os

from dropbox.files import WriteMode, FileMetadata
from dropbox.exceptions import ApiError, AuthError

from ApiWrapper import ApiWrapper


class DropboxWrapper(ApiWrapper):
    def __init__(self,  apitoken):
        self.__dbx = dropbox.Dropbox(apitoken)
        try:
            self.__dbx.users_get_current_account()
        except AuthError as err:
            raise Exception("Invalid dropbox api token!")

    def uploadFile(self, localPath, remotePath):
        lastModified = datetime.datetime.fromtimestamp(os.stat(localPath).st_mtime)
        with open(localPath, 'rb') as f:
            data = f.read()
            self.__dbx.files_upload(data, remotePath, mode=WriteMode('overwrite'), client_modified=lastModified)
            
    def downloadFile(self, localPath, remotePath):
        self.__createLocalPath(remotePath)
        self.__dbx.files_download_to_file(localPath, remotePath)

    def __createLocalPath(self, path):
        path = path.lstrip('/').split('/')
        targetDirs = "/".join(path[:-1])
        fullPath = '/opt/remoteSyncDir/{}'.format(targetDirs)
        if not os.path.exists(fullPath):
            os.makedirs(fullPath)

    def deleteFile(self, path):
        self.__dbx.files_delete('/{}'.format(path))

    def getFilelist(self):
        fileList = []
        for entry in self.__dbx.files_list_folder('', recursive=True).entries:
            entryIsEncryptedFile = isinstance(entry, FileMetadata) #and entry.name.find('.enc') != -1:
            if entryIsEncryptedFile:
                entry.name = entry.name.split('.enc')[0]
                path = entry.path_display.split('.enc')[0]
                fileList.append({
                    "path": path.lstrip('/'),
                    "fileName": entry.name,
                    "lastModified": int(time.mktime(datetime.datetime.timetuple(entry.client_modified))),
                    "size": entry.size
                })
        return fileList

    def moveFile(self, sourcePath, destinationPath):
        self.__dbx.files_move('/{}'.format(sourcePath),'/{}'.format(destinationPath))