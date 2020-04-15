import re

from dataclasses import dataclass, field
from typing import List
from enum import IntEnum

from control.abstract import Singleton


class FileStatuses(IntEnum):
    DOWNLOADING_FROM_CLOUD = 0
    UPLOADING_TO_CLOUD = 1
    DOWNLOADING_TO_LOCAL = 2
    UPLOADING_FROM_LOCAL = 3
    SYNCED = 4
    MOVING = 5


@dataclass
class FileData:
    filename: str
    modified: int
    size: int
    path: str
    fullPath: str
    extraInfo: object = None

    def serialize(self):
        return {"filename": self.filename, "modified": self.modified, "size": self.size, "path": self.path, "fullPath": self.fullPath}


@dataclass
class FilePart:
    partName: str
    storingAccountID: int
    size: int
    extraInfo: object = None


@dataclass
class CachedFileData:
    data: FileData
    availablePartCount: int
    totalPartCount: int
    parts: List[FilePart]


class CloudFilesCache(metaclass=Singleton):

    def __init__(self):
        self.__filesCache = {}
        self.__partPattern = "(__[0-9]+){2}\.enc"
        self.__totalCountPattern = "__[0-9]+"

    def clearData(self):
        self.__filesCache = {}

    def insertFilePart(self, filePart, accountID):
        realFilename = self.__getRealFilename(filePart.filename)
        realFileFullPath = f"{filePart.path}/{realFilename}" if len(filePart.path) > 0 else realFilename
        try:
            self.__filesCache[realFileFullPath].data.size += filePart.size - 16
            self.__filesCache[realFileFullPath].availablePartCount += 1
            self.__filesCache[realFileFullPath].parts.append(FilePart(filePart.filename, filePart.size, accountID, filePart.extraInfo))
        except KeyError:
            partName = filePart.filename
            filePart.filename = realFilename
            filePart.fullPath = realFileFullPath
            self.__filesCache[realFileFullPath] = CachedFileData(filePart, 1, self.__getFilePartCount(partName), [FilePart(partName, accountID, filePart.size, filePart.extraInfo)])
            self.__filesCache[realFileFullPath].data.size -= 16

    def removeFile(self, path):
        del self.__filesCache[path]

    def getFile(self, path):
        return self.__filesCache.get(path)

    def __getRealFilename(self, filePartName):
        match = re.search(self.__partPattern, filePartName)
        matchStartIndex = match.span()[0]

        return filePartName[:matchStartIndex]

    def __getFilePartCount(self, filePartName):
        match = re.findall(self.__totalCountPattern, filePartName)

        return int(match[1].split("__")[1])

    def getFullFiles(self):
        fullFiles = [cachedFile.data.serialize() for key, cachedFile in self.__filesCache.items() if cachedFile.availablePartCount == cachedFile.totalPartCount]
        return fullFiles

    def getIncompleteFiles(self):
        return [f"{cachedFile.data.fullPath} (missing part count: {cachedFile.totalPartCount - cachedFile.availablePartCount})" for key, cachedFile in self.__filesCache.items() if cachedFile.totalPartCount > cachedFile.availablePartCount]
