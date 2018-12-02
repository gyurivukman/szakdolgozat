import Queue
import shutil
import os
import time

from PyQt4 import QtCore

from src.model.FileTask import FileTask, FileTaskType
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
        self.__taskHandlers[FileTaskType.UPLOAD] = self.__uploadFile
        self.__taskHandlers[FileTaskType.EXISTENCE_CHECK] = self.__checkForFile
        self.__taskHandlers[FileTaskType.DELETE] = self.__deleteRemoteFile

    def __startFileScanner(self):
        #TODO init file list here!
        self.__fileScannerThread.start()

    def __handleCurrentTask(self):
        (self.__taskHandlers[self.__currentTask.getType()])()
        self.__readyForNextTask = True

    def __newFileEventHandler(self, task):
        self.__taskQueue.put(task)

    def __commReportHandler(self, report):
        if report["todo"] == FileTaskType.UPLOAD or report["todo"] == FileTaskType.DOWNLOAD:
            sshTask = FileTask(report["todo"], report["data"].getTargetDir(), report["data"].getFullPath(), report["data"].getFileName())
            self.sshManager.enqueuTask(sshTask)

    def __checkForFile(self):
        self.__commService.enqueuFileStatusTask(self.__currentTask)

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
