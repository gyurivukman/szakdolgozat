import Queue
import time

import paramiko
from PyQt4 import QtCore

from src.model.FileTask import TaskType


class SSHManager(QtCore.QObject):
    taskReportChannel = QtCore.pyqtSignal()

    def __init__(self):
        super(SSHManager, self).__init__()
        self.__setup()
        self.__initTaskHandlers()
        self.__initSFTP()

    def __setup(self):
        self.shouldRun = True
        self.queue = Queue.Queue()
        self.__currentTask = None
        self.settings = QtCore.QSettings()

    def __initTaskHandlers(self):
        self.taskHandlers = {
            TaskType.UPLOAD: self.__uploadHandler,
            TaskType.DOWNLOAD: self.__downloadHandler,
        }

    def __initSFTP(self):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(
            unicode(self.settings.value("SSH_Address").toString()),
            self.settings.value("SSH_Port").toInt()[0],
            username=unicode(self.settings.value("SSH_username").toString()),
            password=unicode(self.settings.value("SSH_password").toString())
        )
        self.__sshTransport = ssh.get_transport()
        self.__sftpClient = ssh.open_sftp()
        try:
            self.__sftpClient.chdir('remoteSyncDir')
        except IOError:
            self.__sftpClient.mkdir('remoteSyncDir')
            self.__sftpClient.chdir('remoteSyncDir')
        finally:
            self.remoteSyncBaseDir = self.__sftpClient.getcwd()

    def start(self):
        while(self.shouldRun):
            if not self.queue.empty():
                self.__currentTask = self.queue.get()
                self.__handleCurrentTask()
            else:
                time.sleep(5)
                print "Sending keepalive packet..."
                self.__sshTransport.send_ignore(10)

    def stop(self):
        self.shouldRun = False

    def getCurrentTask(self):
        return self.__currentTask

    def enqueuTask(self, task):
        self.queue.put(task)

    def __handleCurrentTask(self):
        self.taskHandlers[self.__currentTask.getType()]()

    def __uploadHandler(self):
        print "UPLOAD"

    def __downloadHandler(self):
        print "DOWNLOADHANDLER"

    def __createDirectoriesOnRemoteHost(self, targetPath):
        if targetPath:
            syncDirRoot = self.__sftpClient.getcwd()
            splittedPath = targetPath.split('/')
            for directory in splittedPath:
                self.__createDirectory(directory)
            self.__sftpClient.chdir(syncDirRoot)

    def __createDirectory(self, directory):
        try:
            self.__sftpClient.stat(directory)
        except IOError:
            self.__sftpClient.mkdir(directory)
            self.__sftpClient.chdir(directory)
