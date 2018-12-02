

class FileDescription(object):
    def __init__(self, **kwargs):
        self.__targetDir = kwargs["targetDir"]
        self.__fullPath = kwargs["fullPath"]
        self.__fileName = kwargs["fileName"]
        self.__lastModified = kwargs["lastModified"]
        self.__size = kwargs["size"]

    @property
    def targetDir(self):
        return self.__targetDir

    @property
    def fullPath(self):
        return self.__fullPath

    @property
    def fileName(self):
        return self.__fileName

    @property
    def relativePath(self):
        return self.__targetDir + "/" + self.__fileName

    @property
    def lastModified(self):
        return self.__lastModified

    @property
    def size(self):
        return self.__size


    @targetDir.setter
    def targetDIr(self, targetDir):
        self.__targetDir = targetDir

    @fullPath.setter
    def fullPath(self, fullPath):
        self.__fullPath = fullPath

    @fileName.setter
    def fileName(self, fileName):
        self.__fileName = fileName

    @lastModified.setter
    def lastModified(self, lastModified):
        self.__lastModified = lastModified

    @size.setter
    def size(self, size):
        self.__size = size
