import Queue
import shutil
import os
import time

from PyQt4 import QtCore

from src.model.FileDescription import FileDescription
from src.model.ConnectionEvent import ConnectionEvent
from src.model.Task import Task, TaskTypes
from FileScanner import FileScanner


class TaskManager(QtCore.QObject):
    fileStatusChannel = QtCore.pyqtSignal(object)
    connectionStatusChannel = QtCore.pyqtSignal(object)

    def __init__(self, sshManager, commService):
        super(TaskManager, self).__init__()
        self.__shouldRun = True
        self.__taskQueue = Queue.Queue()
        self.__readyForNextTask = True
        self.__setupServices(sshManager, commService)
        self.__initTaskHandlers()

    def start(self):
        self.__startFileScanner()
        while(self.__shouldRun):
            if not self.__taskQueue.empty() and self.__readyForNextTask:
                self.__currentTask = self.__taskQueue.get()
                self.__readyForNextTask = False
                self.__handleCurrentTask()
            else:
                time.sleep(4)

    def __setupServices(self, sshManager, commService):
        self.__setupFileScanner()
        self.__setupSSHManager(sshManager)
        self.__setupCommService(commService)

    def __setupFileScanner(self):
        self.__fileScanner = FileScanner()
        self.__fileScanner.newFileChannel.connect(self.__newFileEventHandler)
        self.__fileScannerThread = QtCore.QThread()
        self.__fileScanner.moveToThread(self.__fileScannerThread)
        self.__fileScannerThread.started.connect((self.__fileScanner).start)

    def __setupSSHManager(self, sshManager):
        self.sshManager = sshManager
        self.sshManager.connectionStatusChannel.connect(self.__connectionStatusHandler)
        #TODO reportChannelSub for SSH status!

    def __setupCommService(self, commService):
        self.__commService = commService
        self.__commService.taskReportChannel.connect(self.__commReportHandler)
        self.__commService.connectionStatusChannel.connect(self.__connectionStatusHandler)

    def __initTaskHandlers(self):
        self.__taskHandlers = {}
        self.__taskHandlers[TaskTypes.UPLOAD] = self.__uploadFile
        self.__taskHandlers[TaskTypes.EXISTENCE_CHECK] = self.__checkForFile
        # self.__taskHandlers[TaskTypes.DELETE] = self.__deleteRemoteFile

    def __startFileScanner(self):
        initialFileList = self.__commService.getInitialFileList()
        print "received initialFileList"
        #TODO: syncInitialFiles -> return the synced list to emit towards uploadswidget
        syncedFileList = self.__fileScanner.syncInitialFileList(initialFileList)
        self.connectionStatusChannel.emit(ConnectionEvent("Sync", True))
        self.__fileScannerThread.start()

    def __handleCurrentTask(self):
        (self.__taskHandlers[self.__currentTask.taskType])()
        self.__readyForNextTask = True

    def __newFileEventHandler(self, task):
        self.__taskQueue.put(task)

    def __commReportHandler(self, report):
        taskType = report.taskType
        if taskType == TaskTypes.UPLOAD:
            self.sshManager.enqueuTask(report)

    def __checkForFile(self):
        self.__commService.enqueuTask(self.__currentTask)

    def __deleteRemoteFile(self):
        print "I SHOULD DELETE REMOTE FILE"
        pass

    def __uploadFile(self, task):
        self.sshManager.enqueuTask(task)

    def __connectionStatusHandler(self, report):
        self.connectionStatusChannel.emit(report)

    def stop(self):
        self.__shouldRun = False
        self.__fileScanner.stop()
        self.__fileScannerThread.quit()
