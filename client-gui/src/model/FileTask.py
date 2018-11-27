from enum import Enum


class FileTask(object):

    def __init__(self, taskType, targetDir, fullPath, fileName):
        self.__taskType = taskType
        self.__targetDir = targetDir
        self.__fileName = fileName
        self.__fullPath = fullPath
        self.__status = FileTaskStatus.INIT

    def getType(self):
        return self.__taskType

    def getTargetDir(self):
        return self.__targetDir

    def getFileName(self):
        return self.__fileName

    def getFullPath(self):
        return self.__fullPath

    def setStatus(self, status):
        self.__status = status

    def setType(self, taskType):
        self.__taskType = taskType

    def __repr__(self):
        return unicode({"taskType": self.__taskType, "targetDir": self.__targetDir, "fileName": self.__fileName, "fullPath": self.__fullPath}).encode("utf8")


class FileTaskType(Enum):
    UPLOAD = 1
    DOWNLOAD = 2
    EXISTENCE_CHECK = 3
    DELETE = 4
    IGNORE = 5


class FileTaskStatus(Enum):
    INIT = 0
    IN_PROGRESS = 1
    DONE = 2
