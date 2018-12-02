import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

TOKEN = 'r8WZ-fi_FEAAAAAAAAAAFy-svElCXZ6XEFMrwD9JMHEui0T_BuifK90JgusB8pSe'


class DropboxWrapper(object):
    def __init__(self, ip, username, passwd):
        self.username = username
        self.passwd = passwd
        if (len(TOKEN) == 0):
            sys.exit("ERROR: Looks like you didn't add your access token. "
            "Open up backup-and-restore-example.py in a text editor and "
            "paste in your token in line 14.")
        self.dbx = dropbox.Dropbox(TOKEN)
        try:
            self.dbx.users_get_current_account()
        except AuthError as err:
            sys.exit("ERROR: Invalid access token; try re-generating an "
            "access token from the app console on the web.")

    def uploadFile(self, upload_path, filename):
        with open(filename, 'rb') as f:
            print("Uploading " + filename + " to Dropbox as " + "/"+upload_path+"/"+filename + "...")
            try:
               self.dbx.files_upload(f.read(), "/"+upload_path+"/"+filename, mode=WriteMode('overwrite'))
            except ApiError as err:
                # This checks for the specific error where a user doesn't have
                # enough Dropbox space quota to upload this file
                if (err.error.is_path() and
                    err.error.get_path().reason.is_insufficient_space()):
                    print(err.user_message_text)
                elif err.user_message_text:
                    print(err.user_message_text)
                else:
                    print(err)

    def downloadFile(self, upload_path, filename):
        print("Downloading current /" + upload_path +"/"+ filename + " from Dropbox, overwriting " + filename + "...")
        self.dbx.files_download_to_file(filename, "/"+upload_path+"/"+filename)

    def deleteFile(self, upload_path, filename):
        print("Deleting file " + filename)
        self.dbx.files_delete("/"+upload_path+"/"+filename)

    def getFilelist(self):
        filelist = []
        ret = {}
        filelist = self.dbx.files_list_folder('/files').entries
        for entry in filelist:
            if entry.name.find('.enc') != -1:
                entry.name=entry.name.split('.enc')[0]
                ret[entry.name] = []
                ret[entry.name].append(entry.server_modified.strftime("%b %d %H:%M"))
                ret[entry.name].append(entry.size)
return ret