import Queue
import shutil
import os
import time

from PyQt4 import QtCore

from src.model.FileDescription import FileDescription
from src.model.ConnectionEvent import ConnectionEvent
from src.model.Task import Task, TaskTypes

from FileScanner import FileScanner
from SSHManager import SSHManager
from CommunicationService import CommunicationService


class TaskManager(QtCore.QObject):
    fileStatusChannel = QtCore.pyqtSignal(object)
    connectionStatusChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(TaskManager, self).__init__()
        self.__shouldRun = True
        self.__taskQueue = Queue.Queue()
        self.__readyForNextTask = True
        self.__connectionStates = {
            "Comm": False,
            "SSH": False,
            "Sync": False
        }
        self.__initTaskHandlers()
        self.__setupServices()

    def start(self):
        while(self.__shouldRun):
            if not self.__taskQueue.empty() and self.__readyForNextTask:
                self.__currentTask = self.__taskQueue.get()
                self.__readyForNextTask = False
                self.__handleCurrentTask()
            else:
                time.sleep(3)

    def init(self, accountData=None):
        if accountData:
            self.__taskQueue.put(Task(taskType=TaskTypes.UPLOAD_ACCOUNTS, subject=accountData))
        self.__taskQueue.put(Task(taskType=TaskTypes.SYNCFILELIST, subject=None))

    def __setupServices(self):
        settings = QtCore.QSettings()
        isFirstStart = not settings.contains('is_first_start') or settings.contains('is_first_start') and settings.value('is_first_start').toBool()

        if not isFirstStart:
            self.__setupDependentServices()
        self.__setupCommService()
        self.__commServiceThread.start()

    def __setupDependentServices(self):
        self.__setupFileScanner()
        self.__setupSSHManager()

    def __setupFileScanner(self):
        self.__fileScanner = FileScanner()
        self.__fileScanner.fileStatusChangeChannel.connect(self.__fileEventHandler)
        self.__fileScannerThread = QtCore.QThread()
        self.__fileScanner.moveToThread(self.__fileScannerThread)
        self.__fileScannerThread.started.connect((self.__fileScanner).start)

    def __setupSSHManager(self):
        self.__sshManager = SSHManager()
        self.__sshManager.connectionStatusChannel.connect(self.__connectionStatusChangeHandler)
        self.__sshManagerThread = QtCore.QThread()
        self.__sshManager.moveToThread(self.__sshManagerThread)
        self.__sshManagerThread.started.connect((self.__sshManager).start)

    def __setupCommService(self):
        self.__commService = CommunicationService()
        self.__commService.connectionStatusChannel.connect(self.__connectionStatusChangeHandler)
        self.__commService.taskReportChannel.connect(self.__commReportHandler)
        self.__commServiceThread = QtCore.QThread()
        self.__commService.moveToThread(self.__commServiceThread)
        self.__commServiceThread.started.connect((self.__commService).start)

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
        self.__taskQueue.task_done()
        self.__readyForNextTask = True

    def __fileEventHandler(self, task):
        pass
        # self.__taskQueue.put(task)

    def __commReportHandler(self, report):
        taskType = report.taskType
        if taskType == TaskTypes.UPLOAD:
            self.__sshManager.enqueuTask(report)
        elif taskType == TaskTypes.SYNCFILELIST:
            syncedFilelist = self.__fileScanner.syncInitialFileList(report.subject) #TODO maybe data instead of subject?
            if not self.__fileScannerThread.isRunning():
                self.__fileScannerThread.start()
            if not self.__sshManagerThread.isRunning():
                self.__sshManagerThread.start()
            self.__connectionStates["Sync"] = True
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
        self.__commService.enqueuTask(self.__currentTask)

    def __syncFiles(self):
        self.__commService.enqueuTask(self.__currentTask)
        self.__readyForNextTask = True

    def __uploadFile(self, task):
        self.__sshManager.enqueuTask(task)

    def __connectionStatusChangeHandler(self, report):
        self.__connectionStates[report.subject] = report.value

        if report.value is False:
            self.__connectionStates["Sync"] = False
            self.connectionStatusChannel.emit(ConnectionEvent("Sync", False))
        #TODO Some disconnection handling here
        self.connectionStatusChannel.emit(report)

    def __restartFileScanner(self):
        with self.__taskQueue.mutex:
            self.__taskQueue.queue.clear()
        self.__taskQueue.put(Task(taskType=TaskTypes.SYNCFILELIST, subject=None))
        self.__readyForNextTask = True

    def stop(self):
        self.__shouldRun = False
        self.__commService.stop()
        self.__sshManager.stop()
        self.__fileScanner.stop()
