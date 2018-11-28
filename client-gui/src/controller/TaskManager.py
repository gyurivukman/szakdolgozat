import Queue
import shutil
import os
import time

from PyQt4 import QtCore

from src.model.FileTask import FileTask, FileTaskType


class TaskManager(QtCore.QObject):
    fileStatusChannel = QtCore.pyqtSignal(object)

    def __init__(self, sshManager, fileScanner, commService):
        super(TaskManager, self).__init__()
        self.shouldRun = True
        self.__taskQueue = Queue.Queue()
        self.__readyForNextTask = True
        self.__setupServices(sshManager, fileScanner, commService)
        self.__initTaskHandlers()

    def start(self):
        while(self.shouldRun):
            if not self.__taskQueue.empty() and self.__readyForNextTask:
                self.__currentTask = self.__taskQueue.get()
                self.__readyForNextTask = False
                self.__handleCurrentTask()
            else:
                time.sleep(4)

    def __setupServices(self, sshManager, fileScanner, commService):
        self.sshManager = sshManager
        self.commService = commService

        self.fileScanner = fileScanner
        self.fileScanner.newFileChannel.connect(self.__newFileFoundHandler)

    def __initTaskHandlers(self):
        self.__taskHandlers = {}
        self.__taskHandlers[FileTaskType.EXISTENCE_CHECK] = self.__checkForFile
        self.__taskHandlers[FileTaskType.DELETE] = self.__deleteRemoteFile

    def __handleCurrentTask(self):
        (self.__taskHandlers[self.__currentTask.getType()])()
        self.__readyForNextTask = True

    def __newFileFoundHandler(self, task):
        self.__taskQueue.put(task)

    def __checkForFile(self):
        relativePath = self.__currentTask.getTargetDir() + '/' + self.__currentTask.getFileName()
        filestatus = self.commService.getFileStatus(relativePath)

        if filestatus == FileTaskType.UPLOAD or filestatus == FileTaskType.DOWNLOAD:
            sshTask = FileTask(filestatus, self.__currentTask.getTargetDir(), self.__currentTask.getFullPath(), self.__currentTask.getFileName())
            self.sshManager.enqueuTask(sshTask)

    def __deleteRemoteFile(self):
        print "I SHOULD DELETE REMOTE FILE"
        pass

    def stop(self):
        self.shouldRun = False