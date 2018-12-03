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
        self.__taskQueue.put(Task(taskType=TaskTypes.SYNCFILELIST, subject=None))
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
        self.__fileScannerThread.setTerminationEnabled(True)
        self.__fileScanner.moveToThread(self.__fileScannerThread)
        self.__fileScannerThread.started.connect((self.__fileScanner).start)
        self.__fileScannerThread.finished.connect(self.__resetFileScanner)

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
        self.__taskHandlers[TaskTypes.DOWNLOAD] = self.__downloadFile
        self.__taskHandlers[TaskTypes.EXISTENCE_CHECK] = self.__checkForFile
        self.__taskHandlers[TaskTypes.SYNCFILELIST] = self.__syncFiles
        self.__taskHandlers[TaskTypes.DELETEFILE] = self.__deleteRemoteFile
        self.__taskHandlers[TaskTypes.PROGRESS_CHECK] = self.__progressCheck
        self.__taskHandlers[TaskTypes.UPLOAD_ACCOUNTS] = self.__uploadAccounts

    def __handleCurrentTask(self):
        (self.__taskHandlers[self.__currentTask.taskType])()
        self.__readyForNextTask = True

    def __newFileEventHandler(self, task):
        self.__taskQueue.put(task)

    def __commReportHandler(self, report):
        taskType = report.taskType
        if taskType == TaskTypes.UPLOAD:
            self.sshManager.enqueuTask(report)
        elif taskType == TaskTypes.SYNCFILELIST:
            syncedFilelist = self.__fileScanner.syncInitialFileList(report.subject) #TODO maybe data instead of subject?
            self.__fileScannerThread.start()
            self.connectionStatusChannel.emit(ConnectionEvent("Sync", True))
            #TODO EMIT THIS TO UPLOADS COMP. TOO

    def __checkForFile(self):
        self.__commService.enqueuTask(self.__currentTask)

    def __progressCheck(self):
        print "PROGRESS CHECK TASK"

    def __deleteRemoteFile(self):
        print "I SHOULD DELETE REMOTE FILE"
    
    def __downloadFile(self):
        print "I SHOULD DOWNLOAD A FILE"
    
    def __uploadAccounts(self):
        print "Upload Accounts!"

    def __syncFiles(self):
        self.__commService.enqueuTask(self.__currentTask)
        self.__readyForNextTask = True

    def __uploadFile(self, task):
        self.sshManager.enqueuTask(task)

    def __connectionStatusHandler(self, report):
        self.connectionStatusChannel.emit(report)
        if report.value == False:
            self.connectionStatusChannel.emit(ConnectionEvent("Sync", False))
            self.__fileScanner.stop()
            self.__fileScannerThread.terminate()
            # self.__resetFileScanner()

    def __resetFileScanner(self):
        self.__setupFileScanner()
        self.__taskQueue.put(Task(taskType=TaskTypes.SYNCFILELIST, subject=None))

    def stop(self):
        self.__shouldRun = False
        self.__fileScanner.stop()
