import Queue
import time
import os
import shutil 

import paramiko
from PyQt4 import QtCore

from src.model.ConnectionEvent import ConnectionEvent
from src.model.Task import TaskTypes


class SSHManager(QtCore.QObject):
    taskReportChannel = QtCore.pyqtSignal(object)
    connectionStatusChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(SSHManager, self).__init__()
        self.__setup()
        self.__initTaskHandlers()

    def __setup(self):
        self.shouldRun = True
        self.__queue = Queue.Queue()
        self.__currentTask = None
        self.settings = QtCore.QSettings()

    def __initTaskHandlers(self):
        self.taskHandlers = {
            TaskTypes.UPLOAD: self.__uploadHandler,
            TaskTypes.DOWNLOAD: self.__downloadHandler,
        }

    def __initSFTP(self):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(
            unicode(self.settings.value("remoteAddress").toString()),
            self.settings.value("SSH_Port").toInt()[0],
            username=unicode(self.settings.value("SSH_username").toString()),
            password=unicode(self.settings.value("SSH_password").toString())
        )
        self.__sshTransport = ssh.get_transport()
        self.__sftpClient = ssh.open_sftp()
        try:
            self.__sftpClient.chdir('/tmp/remoteSyncDir')
        except IOError:
            self.__sftpClient.chdir('/tmp')
            self.__sftpClient.mkdir('remoteSyncDir')
            self.__sftpClient.chdir('remoteSyncDir')
        finally:
            self.__remoteSyncdirRoot = self.__sftpClient.getcwd()

    def __cleanRemoteSyncDir(self):
        for root, dirs, files in os.walk(self.__remoteSyncdirRoot):
            for f in files:
                self.__sftpClient.remove(os.path.join(root, f))
            for d in dirs:
                self.__sftpClient.remove(os.path.join(root, d))
        print "Successfully cleaned remote."

    def start(self):
        self.__initSFTP()
        self.__cleanRemoteSyncDir()
        self.connectionStatusChannel.emit(ConnectionEvent("SSH", True))
        while(self.shouldRun):
            if not self.__queue.empty():
                self.__currentTask = self.__queue.get()
                self.__handleCurrentTask()
            else:
                self.__sshTransport.send_ignore(10)                
                time.sleep(5)

    def stop(self):
        self.shouldRun = False

    def enqueuTask(self, task):
        self.__queue.put(task)

    def __handleCurrentTask(self):
        self.taskHandlers[self.__currentTask.taskType]()

    def __uploadHandler(self):
        self.__navigateToTargetDirectoryOnRemoteHost()
        self.__uploadFile()

    def __downloadHandler(self):
        print "DOWNLOADHANDLER"

    def __navigateToTargetDirectoryOnRemoteHost(self):
        if self.__currentTask.subject.targetDir != "/":
            splittedPath = (self.__currentTask.subject.targetDir.lstrip("/").split('/'))
            for directory in splittedPath:
                self.__navigateToDirectory(directory)

    def __uploadFile(self):
        print "uploading: "+self.__currentTask.subject.fullPath
        self.__sftpClient.put(self.__currentTask.subject.fullPath, self.__currentTask.subject.fileName, callback=self.__reportProgress)
        print "Upload finished!"
        self.__sftpClient.chdir(self.__remoteSyncdirRoot)

    def __reportProgress(self, transferred, remaining):
        print self.__currentTask.subject.fullPath + " {} / {}".format(transferred, remaining)

    def __navigateToDirectory(self, directory):
        try:
            self.__sftpClient.chdir(directory)
        except IOError:
            self.__sftpClient.mkdir(directory)
            self.__sftpClient.chdir(directory)
