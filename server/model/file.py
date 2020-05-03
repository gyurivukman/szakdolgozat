import re

from dataclasses import dataclass, field
from typing import Dict, Any
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

    def serialize(self):
        return {"filename": self.filename, "modified": self.modified, "size": self.size, "path": self.path, "fullPath": self.fullPath}


@dataclass
class FilePart(FileData):
    storingAccountID: int
    extraInfo: Any = field(default_factory=dict)


@dataclass
class CachedFileData:
    data: FileData
    availablePartCount: int
    totalPartCount: int
    parts: Dict[str, FilePart] = field(default_factory=dict)


class CloudFilesCache(metaclass=Singleton):

    def __init__(self):
        self.__filesCache = {}
        self.__partPattern = "(__[0-9]+){2}\.enc"
        self.__totalCountPattern = "__[0-9]+"

    def clearData(self):
        self.__filesCache = {}

    def insertFilePart(self, filePart):
        realFilename = self.__getRealFilename(filePart.filename)
        realFileFullPath = f"{filePart.path}/{realFilename}" if len(filePart.path) > 0 else realFilename
        try:
            self.__filesCache[realFileFullPath].data.size += filePart.size - 16
            self.__filesCache[realFileFullPath].availablePartCount += 1
            self.__filesCache[realFileFullPath].parts[filePart.filename] = filePart
        except KeyError:
            partName = filePart.filename
            fileData = self.__filePartToFileData(filePart, realFilename, realFileFullPath)
            self.__filesCache[realFileFullPath] = CachedFileData(
                fileData, 1, self.__getFilePartCount(partName), {partName: filePart}
            )

    def removeFile(self, path):
        del self.__filesCache[path]

    def getFile(self, path):
        return self.__filesCache.get(path)

    def getFullFiles(self):
        fullFiles = [cachedFile.data.serialize() for key, cachedFile in self.__filesCache.items() if cachedFile.availablePartCount == cachedFile.totalPartCount]
        return fullFiles

    def getIncompleteFiles(self):
        return [cachedFile for key, cachedFile in self.__filesCache.items() if cachedFile.totalPartCount > cachedFile.availablePartCount]

    def moveFile(self, sourcePath, targetPath):
        self.__filesCache[targetPath] = self.__filesCache[sourcePath]
        del self.__filesCache[sourcePath]

    def __getRealFilename(self, fileName):
        match = re.search(self.__partPattern, fileName)
        matchStartIndex = match.span()[0]

        return fileName[:matchStartIndex]

    def __getFilePartCount(self, filePartName):
        match = re.findall(self.__totalCountPattern, filePartName)

        return int(match[1].split("__")[1])

    def __filePartToFileData(self, filePart, realFilename, realFileFullPath):
        return FileData(
            realFilename,
            filePart.modified,
            filePart.size - 16,
            filePart.path,
            realFileFullPath
        )
