from PyQt4 import QtCore
import Queue
import shutil
import os
import time

from src.model.FileTask import FileTask, TaskType


class FileManager(QtCore.QObject):

    def __init__(self, networkManager, fileScanner):
        super(FileManager, self).__init__()
        self.shouldRun = True
        self.__readyForNextTask = True
        self.networkManager = networkManager
        self.networkManager.taskReportChannel.connect(self.__taskReportHandler)

        self.fileScanner = fileScanner
        self.fileScanner.newFileChannel.connect(self.__newFileHandler)
        self.eventQueue = Queue.Queue()

    def start(self):
        while(self.shouldRun):
            if not self.eventQueue.empty() and self.__readyForNextTask:
                self.__currentTask = self.eventQueue.get()
                self.__readyForNextTask = False
                self.__handleCurrentTask()
            else:
                time.sleep(4)

    def __handleCurrentTask(self):
        print "handling current task..."
        time.sleep(5)
        self.__currentTask = None
        self.__readyForNextTask = True

    def __taskReportHandler(self, taskReport):
        print taskReport

    def __newFileHandler(self, report):
        print "new file handler"
        print report

    def stop(self):
        self.shouldRun = False
