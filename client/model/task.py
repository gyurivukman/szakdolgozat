from dataclasses import dataclass
from typing import Any

from model.file import FileStatuses


GLOBAL_FILE_TASK_ARCHIVE = {}


@dataclass
class FileTask:
    uuid: str
    taskType: FileStatuses
    subject: Any
    destinationPath: str = None
    stale: bool = False
