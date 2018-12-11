import Queue
import time
import os

import src.model.MessageTypes as MessageTypes
import src.model.TaskStatus as TaskStatus
from src.controller.DatabaseAccessObject import DatabaseAccessObject
from src.controller.CloudAPIStore import CloudAPIStore


class LongTaskWorker(object):

    def __init__(self, taskReports):
        self.__taskReports = taskReports
        self.__taskQueu = Queue.Queue()
        self.__shouldRun = True
        dbo = DatabaseAccessObject()
        self.__accounts = dbo.getAccounts()
        self.__apiStore = CloudAPIStore()
        #TODO FileEncoder

    def enqueueDownloadFileTask(self, message):
        data = message["data"]
        self.__taskQueu.put({"subject": data, "taskType": MessageTypes.DOWNLOAD_FILE})
        self.__taskReports[data["path"]] = TaskStatus.IN_QUEUE_FOR_DOWNLOAD
        return {"type": "ack"}

    def enqueueUploadFileTask(self, message):
        data = message["data"]
        self.__taskQueu.put({"subject": data, "taskType": MessageTypes.UPLOAD_FILE})
        self.__taskReports[data["path"]] = TaskStatus.UPLOADING_TO_CLOUD
        return {"type": "ack"}

    def run(self):
        while self.__shouldRun:
            if not self.__taskQueu.empty():
                task = self.__taskQueu.get()
                if task["taskType"] == MessageTypes.DOWNLOAD_FILE:
                    self.__downloadFile(task["subject"])
                else:
                    self.__uploadFile(task["subject"])

    def __downloadFile(self, data):
        self.__taskReports[data["path"]] = TaskStatus.DOWNLOADING_FROM_CLOUD
        api = self.__apiStore.getAPIWrapper(self.__accounts[0])
        api.downloadFile(data["fileName"], data["path"])
        time.sleep(3)
        self.__taskReports[data["path"]] = TaskStatus.DECRYPTING
        time.sleep(3)
        self.__taskReports[data["path"]] = TaskStatus.DOWNLOADING_FROM_REMOTE

    def __uploadFile(self, data):
        self.__taskReports[data["path"]] = TaskStatus.ENCRYPTING
        time.sleep(5)
        for account in self.__accounts:
            api = self.__apiStore.getAPIWrapper(account)
            api.uploadFile(data["fileName"], data["path"])
        self.__removeTemporaryFile(data["fileName"])
        self.__taskReports[data["path"]] = TaskStatus.SYNCED

    def __removeTemporaryFile(self, targetFile):
        os.remove('/opt/remoteSyncDir/{}'.format(targetFile))
