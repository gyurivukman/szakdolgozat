from MessageHandler import MessageHandler
from src.controller.DatabaseAccessObject import DatabaseAccessObject
from src.controller.CloudAPIStore import CloudAPIStore


class GetFileListMessageHandler(MessageHandler):

    def __init__(self):
        self.__dao = DatabaseAccessObject()
        apiStore = CloudAPIStore()
        referenceAccount = self.__dao.getAccounts()[0]
        self.__api = apiStore.getAPIWrapper(referenceAccount)

    def handleMessage(self, message):
        return self.__api.getFilelist()
