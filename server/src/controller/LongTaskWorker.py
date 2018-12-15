import Queue
import time
import os

import src.model.MessageTypes as MessageTypes
import src.model.TaskStatus as TaskStatus
from src.controller.DatabaseAccessObject import DatabaseAccessObject
from src.controller.CloudAPIStore import CloudAPIStore
from src.controller.FileEncoder import FileEncoder


class LongTaskWorker(object):

    def __init__(self, taskReports):
        self.__taskReports = taskReports
        self.__taskQueu = Queue.Queue()
        self.__shouldRun = True
        dbo = DatabaseAccessObject()
        self.__accounts = dbo.getAccounts()
        self.__apiStore = CloudAPIStore()
        self.__fileEncoder = FileEncoder()
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
        localPath = '/opt/remoteSyncDir/{}.enc'.format(data["path"])
        cloudPath = '/{}.enc'.format(data["path"])
        api.downloadFile(localPath, cloudPath)
        self.__taskReports[data["path"]] = TaskStatus.DECRYPTING
        self.__fileEncoder.decryptFile(localPath)
        self.__taskReports[data["path"]] = TaskStatus.DOWNLOADING_FROM_REMOTE

    def __uploadFile(self, data):
        self.__taskReports[data["path"]] = TaskStatus.ENCRYPTING
        localPath = '/opt/remoteSyncDir/{}'.format(data["path"])
        self.__fileEncoder.encryptFile(localPath)
        for account in self.__accounts:
            api = self.__apiStore.getAPIWrapper(account)
            api.uploadFile('{}.enc'.format(localPath), '/{}.enc'.format(data["path"]))
        self.__taskReports[data["path"]] = TaskStatus.SYNCED
