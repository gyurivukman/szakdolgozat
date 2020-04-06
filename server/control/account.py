import paramiko
import re

from model.file import FileData


class SFTPCloudAccount():

    def __init__(self, accountData):
        self.__accountData = accountData

        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__client.connect("localhost", 22, self.__accountData['username'], self.__accountData['password'])

        self.__sftp = self.__client.open_sftp()

    def getFileList(self):
        raw_files = self.__sftp.listdir_attr("remoteStorage")

        return [
            FileData(raw.filename, raw.st_mtime, raw.st_size, "")
            for raw in raw_files
            if re.match("[a-zA-Z_0-9\.]+\.enc$", raw.filename)
        ]

    def __del__(self):
        self.__sftp.close()
        self.__client.close()
