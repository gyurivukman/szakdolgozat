from dataclasses import dataclass

from model.file import FileStatuses


GLOBAL_FILE_TASK_ARCHIVE = {}


@dataclass
class FileTask:
    uuid: str
    taskType: FileStatuses
    subject: object
    destinationPath: str = None
    stale: bool = False
