from MessageHandler import MessageHandler
from src.controller.CloudAPIStore import CloudAPIStore
from src.controller.DatabaseAccessObject import DatabaseAccessObject


class MoveFileMessageHandler(MessageHandler):

    def __init__(self):
        self.__dao = DatabaseAccessObject()
        self.__apiStore = CloudAPIStore()

    def handleMessage(self, message):
        sourcePath = message["data"]["from"]
        destinationPath = message["data"]["to"]
        accounts = self.__dao.getAccounts()

        for account in accounts:
            api = self.__apiStore.getAPIWrapper(account)
            api.moveFile(sourcePath, destinationPath)

        return {"type": "ack"}
