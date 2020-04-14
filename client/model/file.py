from os import stat
from datetime import datetime

from dataclasses import dataclass, field
from enum import Enum, IntEnum


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
    status: FileStatuses = None

    def serialize(self):
        return {"filename": self.filename, "modified": self.modified, "size": self.size, "path": self.path, "fullPath": self.fullPath}


class FileEventTypes(Enum):
    MODIFIED = "modified"
    CREATED = "created"
    DELETED = "deleted"
    MOVED = "moved"
    STATUS_CHANGED = "status_changed"


@dataclass
class FileStatusEvent:
    eventType: FileEventTypes
    sourcePath: str
    status: FileStatuses = None
    destinationPath: str = None


@dataclass
class CheckLaterFileEvent:
    originalEvent: FileStatusEvent
    timeOfLastAction: datetime
