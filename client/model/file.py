from dataclasses import dataclass, field
from enum import Enum, IntEnum


class FileStatuses(IntEnum):
    DOWNLOADING_FROM_CLOUD = 0
    UPLOADING_TO_CLOUD = 1
    ENCRYPTING = 2
    DECRYPTING = 3
    DOWNLOADING_TO_LOCAL = 4
    UPLOADING_FROM_LOCAL = 5
    SYNCED = 6


@dataclass
class FileData:
    filename: str
    modified: int
    size: int
    path: str
    fullPath: str = None
    status: FileStatuses = None

    def serialize(self):
        return {"filename": self.filename, "modified": self.modified, "size": self.size, "path": self.path}


class FileTaskTypes(Enum):
    MODIFIED = "modified"
    CREATED = "created"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileTask:
    taskType: FileTaskTypes
    subject: FileData
    destinationPath: str = None
