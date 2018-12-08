from MessageHandler import MessageHandler
from src.controller.DatabaseAccessObject import DatabaseAccessObject


class GetFileListMessageHandler(MessageHandler):

    def __init__(self):
        self.__dao = DatabaseAccessObject()

    def handleMessage(self, message):
        rawResult = self.__dao.getAllFiles()
        files = []

        for f in rawResult:
            files.append({
                "fileName": f[1],
                "dir": f[2],
                "path": "{}/{}".format(f[2], f[1]) if f[2]!="" else f[1],
                "size": f[3],
                "lastModified": f[4]
            })
        return files
