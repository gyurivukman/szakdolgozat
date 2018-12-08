import sys
import datetime
import dropbox

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

    def getFileList(self):
        pass

    def uploadFile(self, path):
        with open(path, 'rb') as f:
            print("Uploading " + path + " to Dropbox")
            try:
                self.__dbx.files_upload(f.read(), "/{}".format(path), mode=WriteMode('overwrite'))
            except ApiError as err:
                # This checks for the specific error where a user doesn't have
                # enough Dropbox space quota to upload this file
                if err.error.is_path() and err.error.get_path().reason.is_insufficient_space():
                    print(err.user_message_text)
                elif err.user_message_text:
                    print(err.user_message_text)
                else:
                    print(err)

    def downloadFile(self, path):
        print("Downloading /{} from Dropbox!".format(path))
        filename = path.split('/')[-1]
        self.__dbx.files_download_to_file(filename, "/{}".format(path))

    def deleteFile(self, path):
        print("Deleting file " + path)
        self.__dbx.files_delete("/{}".format(path))

    def getFilelist(self):
        epoch = datetime.datetime(1970, 1, 1)
        fileList = []
        for entry in self.__dbx.files_list_folder('', recursive=True).entries:
            entryIsEncryptedFile = isinstance(entry, FileMetadata) #and entry.name.find('.enc') != -1:
            if entryIsEncryptedFile:
                entry.name = entry.name.split('.enc')[0]
                path = entry.path_display
                fileList.append({
                    "path": path.lstrip('/'),
                    "dir": path.split('/')[-2],
                    "fileName": entry.name,
                    "lastModified":(entry.client_modified - epoch).total_seconds(),
                    "size": entry.size
                })
        return fileList
