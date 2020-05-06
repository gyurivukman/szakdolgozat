import logging

from dataclasses import dataclass
from typing import Any

from model.file import FileStatuses
from services.util import Singleton


GLOBAL_FILE_TASK_ARCHIVE = {}


@dataclass
class FileTask:
    uuid: str
    taskType: FileStatuses
    subject: Any
    stale: bool = False


class TaskArchive(metaclass=Singleton):

    def __init__(self):
        self.__taskStorage = {}
        self.__logger = logging.getLogger(__name__).getChild("TaskArchive")

    def clearAllTasks(self):
        for key, task in self.__taskStorage.items():
            task.stale = True
        self.__taskStorage = {}

    def addTask(self, key, task):
        if type(task) != FileTask:
            raise ValueError(f"Expected type 'FileTask' for argument task. Received {type(task)} instead!")
        self.__taskStorage[key] = task

    def getTask(self, key):
        return self.__taskStorage.get(key, None)

    def removeTask(self, key):
        try:
            del self.__taskStorage[key]
            self.__logger.debug(f"Task removed from key: {key}")
        except KeyError:
            self.__logger.warning(f"Remove task error: Task cannot be found under key: {key}")

    def cancelTask(self, key):
        try:
            self.__taskStorage[key].stale = True
            self.__logger.info(f"Task cancelled under key: {key}")
        except KeyError:
            self.__logger.warning(f"Cancel task error: Task cannot be found under key: {key}")
