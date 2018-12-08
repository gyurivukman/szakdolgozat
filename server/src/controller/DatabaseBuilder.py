from DatabaseAccessObject import DatabaseAccessObject
from CloudAPIStore import CloudAPIStore


class DatabaseBuilder(object):

    def __init__(self):
        self.__dao = DatabaseAccessObject()

    def initDatabase(self):
        referenceAccount = self.__dao.getAccounts()[0]
        apiStore = CloudAPIStore()
        apiWrapper = apiStore.getAPIWrapper(referenceAccount)

        files = apiWrapper.getFilelist()

        for remoteFile in files:
            self.__dao.insertFile(remoteFile)
        print "DB synced successfully!"
