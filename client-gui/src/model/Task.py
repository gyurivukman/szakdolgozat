from enum import Enum


class Task(object):
    def __init__(self, **kwargs):
        self.__taskType = kwargs["taskType"]
        self.__subject = kwargs["subject"]

    @property
    def taskType(self):
        return self.__taskType

    @property
    def subject(self):
        return self.__subject


class TaskTypes(Enum):
    UPLOAD = 0
    DOWNLOAD = 1
    SYNCFILELIST = 2
    DELETEFILE = 3
    EXISTENCE_CHECK = 4
    KEEP_ALIVE = 5
    PROGRESS_CHECK = 6
    UPLOAD_ACCOUNTS = 7
