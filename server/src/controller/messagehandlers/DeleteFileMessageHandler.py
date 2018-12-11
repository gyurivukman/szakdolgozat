from MessageHandler import MessageHandler
from src.controller.CloudAPIStore import CloudAPIStore
from src.controller.DatabaseAccessObject import DatabaseAccessObject


class DeleteFileMessageHandler(MessageHandler):

    def __init__(self):
        self.__dao = DatabaseAccessObject()

    def handleMessage(self, message):
        targetFile = message["data"]
        apiStore = CloudAPIStore()
        accounts = self.__dao.getAccounts()

        for account in accounts:
            api = apiStore.getAPIWrapper(account)
            api.deleteFile(targetFile)

        return {"type": "ack"}
