import logging

from enum import IntEnum
from dataclasses import dataclass

from control.abstract import Singleton


GLOBAL_TASK_ARCHIVE = {}


@dataclass
class Task():
    taskType: int
    stale: bool = False
    uuid: str = None
    data: dict = None


class TaskArchive(metaclass=Singleton):

    def __init__(self):
        self.__taskStorage = {}
        self.__logger = logging.getLogger(__name__).getChild("TaskArchive")

    def clearAllTasks(self):
        for key, task in self.__taskStorage.items():
            task.stale = True
        self.__taskStorage = {}

    def addTask(self, key, task):
        self.__taskStorage[key] = task
        self.__logger.debug(f"Task ({task.uuid}) added under key: {key}")

    def removeTask(self, key):
        try:
            self.__logger.debug(f"Task ({self.__taskStorage[key].uuid}) removed from key: {key}")
            del self.__taskStorage[key]
        except KeyError:
            self.__logger.warning(f"Remove task error: Task cannot be found under key: {key}")

    def cancelTask(self, key):
        try:
            self.__taskStorage[key].stale = True
            self.__logger.info(f"Task ({self.__taskStorage[key].uuid}) cancelled under key: {key}")
        except KeyError:
            self.__logger.warning(f"Cancel task error: Task cannot be found under key: {key}")
