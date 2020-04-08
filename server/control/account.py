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
        stdin, stdout, stderr = self.__client.exec_command("find . -type f -name \\*.enc -printf '%T@ %s %P %p\n'")

        fileList = []

        for line in stdout:
            splitted = line.split(" ")
            modified = int(float(splitted[0]))
            size = int(splitted[1])
            filename = splitted[2]
            fullPath = splitted[3][1:-1]
            path = fullPath.replace(f"/{filename}", "")

            fileList.append(FileData(filename, modified, size, path, fullPath))

        return fileList

    def __del__(self):
        self.__sftp.close()
        self.__client.close()
