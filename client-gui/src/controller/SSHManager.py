import Queue
import time

import paramiko
from PyQt4 import QtCore

from src.model.FileTask import FileTaskType


class SSHManager(QtCore.QObject):
    taskReportChannel = QtCore.pyqtSignal()

    def __init__(self):
        super(SSHManager, self).__init__()
        self.__setup()
        self.__initTaskHandlers()
        self.__initSFTP()

    def __setup(self):
        self.shouldRun = True
        self.__queue = Queue.Queue()
        self.__currentTask = None
        self.settings = QtCore.QSettings()

    def __initTaskHandlers(self):
        self.taskHandlers = {
            FileTaskType.UPLOAD: self.__uploadHandler,
            FileTaskType.DOWNLOAD: self.__downloadHandler,
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
            self.__sftpClient.chdir('remoteSyncDir')
        except IOError:
            self.__sftpClient.mkdir('remoteSyncDir')
            self.__sftpClient.chdir('remoteSyncDir')
        finally:
            self.remoteSyncBaseDir = self.__sftpClient.getcwd()

    def start(self):
        while(self.shouldRun):
            if not self.__queue.empty():
                self.__currentTask = self.__queue.get()
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
        self.__queue.put(task)

    def __handleCurrentTask(self):
        self.taskHandlers[self.__currentTask.getType()]()

    def __uploadHandler(self):
        self.__navigateToTargetDirectoryRemoteHost()
        self.__uploadFile()

    def __downloadHandler(self):
        print "DOWNLOADHANDLER"

    def __navigateToTargetDirectoryRemoteHost(self):
        if self.__currentTask.getTargetDir() != "/":
            splittedPath = (self.__currentTask.getTargetDir().lstrip("/").split('/'))
            for directory in splittedPath:
                self.__navigateToDirectory(directory)

    def __uploadFile(self):
        print "uploading: "+self.__currentTask.getFullPath()
        self.__sftpClient.put(self.__currentTask.getFullPath(), self.__currentTask.getFileName(), callback=self.__reportProgress)
        print "Upload finished!"
        self.__sftpClient.chdir(self.remoteSyncBaseDir)

    def __reportProgress(self, transferred, remaining):
        print self.__currentTask.getFullPath() + " {} / {}".format(transferred, remaining)

    def __navigateToDirectory(self, directory):
        try:
            self.__sftpClient.chdir(directory)
        except IOError:
            self.__sftpClient.mkdir(directory)
            self.__sftpClient.chdir(directory)
