from MessageHandler import MessageHandler


class AccountUploadMessageHandler(MessageHandler):

    def handleMessage(self, message):
        "AccountUploadMessageHandler should fill DB with: " + str(message)
        return []