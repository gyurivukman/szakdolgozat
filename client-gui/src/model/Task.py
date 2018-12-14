from enum import Enum


class Task(object):
    def __init__(self, **kwargs):
        self.__taskType = kwargs["taskType"]
        self.__subject = kwargs["subject"]
        self.__status = kwargs["status"]

    @property
    def taskType(self):
        return self.__taskType

    @property
    def subject(self):
        return self.__subject
    
    @property
    def status(self):
        return self.__status
    
    @status.setter
    def status(self, status):
        self.__status = status


class TaskTypes(Enum):
    UPLOAD = 0
    DOWNLOAD = 1
    SYNCFILELIST = 2
    DELETEFILE = 3
    PROGRESS_CHECK = 4
    UPLOAD_ACCOUNTS = 5
    MOVEFILE = 6
    SYNCED = 7
