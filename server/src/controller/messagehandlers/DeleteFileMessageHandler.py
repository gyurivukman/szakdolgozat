from MessageHandler import MessageHandler
from src.controller.CloudAPIStore import CloudAPIStore
from src.controller.DatabaseAccessObject import DatabaseAccessObject


class DeleteFileMessageHandler(MessageHandler):

    def __init__(self):
        self.__dao = DatabaseAccessObject()
        self.__apiStore = CloudAPIStore()

    def handleMessage(self, message):
        targetFile = message["data"]
        accounts = self.__dao.getAccounts()

        for account in accounts:
            api = self.__apiStore.getAPIWrapper(account)
            api.deleteFile('{}.enc'.format(targetFile))

        return {"type": "ack"}
