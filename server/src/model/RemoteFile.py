

class RemoteFile(object):
    def __init__(self, **kwargs):
        self.__dir = kwargs["dir"]
        self.__fileName = kwargs["fileName"]
        self.__lastModified = kwargs["lastModified"]
        self.__size = kwargs["size"]

    @property
    def dir(self):
        return self.__dir

    @dir.setter
    def dir(self, dir):
        self.__dir = dir

    @property
    def fileName(self):
        return self.__fileName

    @fileName.setter
    def fileName(self, fileName):
        self.__fileName = fileName

    @property
    def lastModified(self):
        return self.__lastModified

    @lastModified.setter
    def lastModified(self, lastModified):
        self.__lastModified = lastModified

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, size):
        self.__size = size

    def serializeToJSON(self):
        return {
            "dir": self.__dir,
            "fileName": self.__fileName,
            "lastModified": self.__lastModified,
            "size": self.__size
        }
