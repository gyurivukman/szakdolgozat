from MessageHandler import MessageHandler
from src.controller.DatabaseAccessObject import DatabaseAccessObject
from src.controller.CloudAPIStore import CloudAPIStore


class GetFileListMessageHandler(MessageHandler):

    def __init__(self):
        self.__dao = DatabaseAccessObject()

    def handleMessage(self, message):
        apiStore = CloudAPIStore()
        referenceAccount = self.__dao.getAccounts()[0]
        api = apiStore.getAPIWrapper(referenceAccount)
        return api.getFilelist()
