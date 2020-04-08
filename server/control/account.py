import paramiko
import re

from model.file import FileData


class SFTPCloudAccount():

    def __init__(self, accountData):
        self.username = accountData['username']
        self.password = accountData['password']
        self.id = accountData['id']

        self.__accountData = accountData

        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__client.connect("localhost", 22, self.username, self.password)

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
