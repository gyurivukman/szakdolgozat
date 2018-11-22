from enum import Enum


class FileTask(object):

    def __init__(self, taskType, targetDir, fullPath, fileName):
        self.__taskType = taskType
        self.__targetDir = targetDir
        self.__fileName = fileName
        self.__fullPath = fullPath

    def getType(self):
        return self.__taskType

    def getTargetDir(self):
        return self.__targetDir

    def getFileName(self):
        return self.__fileName
    
    def getFullPath(self):
        return self.__fullPath


class TaskType(Enum):
    UPLOAD = 1
    DOWNLOAD = 2
    EXISTENCE_CHECK = 3
    DELETE = 4
