from apiwrappers.DropBoxWrapper import DropboxWrapper


class CloudAPIStore(object):

    def __init__(self):
        self.__apiStore = {
            "Dropbox": self.__createDropboxAPIWrapper
        }

    def getAPIWrapper(self, account):
        accountType = account["account_type"]
        apiWrapper = None
        if accountType in self.__apiStore:
            apiWrapper = self.__apiStore[account["account_type"]](account)
        return apiWrapper

    def __createDropboxAPIWrapper(self, account):
        apiToken = account["fields"]["token"]
        return DropboxWrapper(apiToken)
