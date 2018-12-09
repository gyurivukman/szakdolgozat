from MessageHandler import MessageHandler
import src.model.TaskStatus as TaskStatus


class ProgressCheckMessageHandler(MessageHandler):
    def __init__(self, taskCache):
        self.__taskCache = taskCache

    def handleMessage(self, message):
        status = None
        if message["data"] in self.__taskCache:
            status = self.__taskCache[message["data"]]
            if status == TaskStatus.SYNCED or status == TaskStatus.DOWNLOADING_FROM_REMOTE:
                del self.__taskCache[message["data"]]

        return {"status": status}
