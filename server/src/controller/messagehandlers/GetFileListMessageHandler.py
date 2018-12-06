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
                "name": f[1],
                "directory": f[2],
                "size": f[3],
                "last_modified": f[4]
            })

        return files
