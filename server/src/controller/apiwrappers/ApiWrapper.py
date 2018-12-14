

class ApiWrapper(object):

    def getFileList(self):
        raise NotImplementedError("method 'getFileList()' not implemented in {}".format(self.__class__))

    def downloadFile(self, path):
        raise NotImplementedError("method 'downloadFile(path)' not implemented in {}".format(self.__class__))

    def uploadFile(self, path):
        raise NotImplementedError("method 'uploadFile' not implemented in {}".format(self.__class__))

    def moveFile(self, sourcePath, destinationPath):
        raise NotImplementedError("method 'moveFile(sourePath, destinationPath)' not implemented in {}".format(self.__class__))

    # def renameFile(self, path, newName):
    #     raise NotImplementedError("method 'renameFile(path, newName)' not implemented in {}".format(self.__class__))

    def deleteFile(self, path):
        raise NotImplementedError("method 'deleteFile(path)' not implemented in {}".format(self.__class__))
