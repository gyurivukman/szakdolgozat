import Queue
import time

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
        targetFile = message["data"]
        self.__taskQueu.put({"subject": targetFile, "taskType": MessageTypes.DOWNLOAD_FILE})
        self.__taskReports[targetFile] = TaskStatus.IN_QUEUE_FOR_DOWNLOAD
        return {"type": "ack"}

    def enqueueUploadFileTask(self, targetFile):
        self.__taskQueu.put({"subject": targetFile, "taskType": MessageTypes.UPLOAD_FILE})
        self.__taskReports[targetFile] = TaskStatus.IN_QUEUE_FOR_UPLOAD
        return {"type": "ack"}

    def run(self):
        while self.__shouldRun:
            if not self.__taskQueu.empty():
                task = self.__taskQueu.get()
                if task["taskType"] == MessageTypes.DOWNLOAD_FILE:
                    self.__downloadFile(task["subject"])
                else:
                    self.__uploadFile(task["subject"])

    def __downloadFile(self, targetFile):
        self.__taskReports[targetFile] = TaskStatus.DOWNLOADING_FROM_CLOUD
        api = self.__apiStore.getAPIWrapper(self.__accounts[0])
        api.downloadFile(targetFile)
        time.sleep(3)
        self.__taskReports[targetFile] = TaskStatus.DECRYPTING
        time.sleep(3)
        self.__taskReports[targetFile] = TaskStatus.DOWNLOADING_FROM_REMOTE

    def __uploadFile(self, targetFile):
        print "server UPLOADING " + targetFile
