import Queue
import time
import datetime
import os
import shutil 

import paramiko
from PyQt4 import QtCore

from src.model.ConnectionEvent import ConnectionEvent
from src.model.Task import TaskTypes
import src.model.TaskStatus as TaskStatus


class SSHManager(QtCore.QObject):
    taskReportChannel = QtCore.pyqtSignal(object)
    connectionStatusChannel = QtCore.pyqtSignal(object)

    def __init__(self):
        super(SSHManager, self).__init__()
        self.__setup()
        self.__initTaskHandlers()

    def __setup(self):
        self.__shouldRun = True
        self.__queue = Queue.Queue()
        self.__currentTask = None
        self.__settings = QtCore.QSettings()
        self.__localSyncDirRoot = unicode(self.__settings.value("syncDir").toString())

    def __initTaskHandlers(self):
        self.taskHandlers = {
            TaskTypes.UPLOAD: self.__uploadHandler,
            TaskTypes.DOWNLOAD: self.__downloadHandler,
        }

    def __initSFTP(self):
        self.__ssh = paramiko.SSHClient()
        self.__ssh.load_system_host_keys()
        self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.__ssh.connect(
            unicode(self.__settings.value("remoteAddress").toString()),
            self.__settings.value("SSH_Port").toInt()[0],
            username=unicode(self.__settings.value("SSH_username").toString()),
            password=unicode(self.__settings.value("SSH_password").toString())
        )
        self.__sshTransport = self.__ssh.get_transport()
        self.__sftpClient = self.__ssh.open_sftp()
        try:
            self.__sftpClient.chdir('/opt/remoteSyncDir')
        except IOError:
            self.__sftpClient.chdir('/opt')
            self.__sftpClient.mkdir('remoteSyncDir')
            self.__sftpClient.chdir('remoteSyncDir')
        finally:
            self.__remoteSyncdirRoot = self.__sftpClient.getcwd()

    def start(self):
        self.__initSFTP()
        self.connectionStatusChannel.emit(ConnectionEvent("SSH", True))
        self.__cleanRemoteSyncDir()
        while self.__shouldRun:
            if not self.__queue.empty():
                self.__currentTask = self.__queue.get()
                self.__handleCurrentTask()
            else:
                self.__sshTransport.send_ignore(10)
                time.sleep(3)

    def stop(self):
        self.__shouldRun = False

    def enqueuTask(self, task):
        self.__queue.put(task)

    def __handleCurrentTask(self):
        self.taskHandlers[self.__currentTask.taskType]()

    def __uploadHandler(self):
        print "Uploading: {} to remote!".format(self.__currentTask.subject["path"])
        self.__sftpClient.put(self.__currentTask.subject["fullPath"], self.__currentTask.subject["fileName"])
        newModificationDate = datetime.datetime.fromtimestamp(int(self.__currentTask.subject["lastModified"])).strftime("%Y%m%d%H%M.%S")
        remotePath = '/opt/remoteSyncDir/{}'.format(self.__currentTask.subject["fileName"])
        self.__ssh.exec_command('touch -mt {} {}'.format(newModificationDate, remotePath))
        self.__ssh.exec_command('chmod ugo+rwx {}'.format(remotePath))
        os.system('touch -mt {} {}'.format(newModificationDate, self.__currentTask.subject["fullPath"]))
        print "SSH Upload finished!"
        self.__currentTask.status = TaskStatus.UPLOADING_TO_CLOUD
        self.taskReportChannel.emit(self.__currentTask)

    def __downloadHandler(self):
        print "Downloading: {} from remote!".format(self.__currentTask.subject["path"])
        self.__createLocalDirs()
        remotePath = '{}/{}'.format(self.__remoteSyncdirRoot, self.__currentTask.subject["fileName"])
        self.__sftpClient.get(remotePath, self.__currentTask.subject["fullPath"])
        newModificationDate = datetime.datetime.fromtimestamp(self.__currentTask.subject["lastModified"]).strftime("%Y%m%d%H%M.%S")
        print "touching it."
        os.system('touch -mt {} {}'.format(newModificationDate, self.__currentTask.subject["fullPath"]))
        self.__removeTemporaryFile()
        print "Download finished!"
        self.__currentTask.status = TaskStatus.SYNCED
        self.taskReportChannel.emit(self.__currentTask)

    def __createLocalDirs(self):
        directory = "/".join(self.__currentTask.subject["fullPath"].split('/')[:-1])
        if not os.path.exists(directory):
            os.makedirs(directory)

    def __cleanRemoteSyncDir(self):
        for root, dirs, files in os.walk(self.__remoteSyncdirRoot):
            for f in files:
                self.__sftpClient.remove(os.path.join(root, f))
            for d in dirs:
                self.__sftpClient.remove(os.path.join(root, d))
        print "Successfully cleaned remote."

    def __removeTemporaryFile(self):
        self.__sftpClient.remove(self.__remoteSyncdirRoot+'/'+self.__currentTask.subject["fileName"])
