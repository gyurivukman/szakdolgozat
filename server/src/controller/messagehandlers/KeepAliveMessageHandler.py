from MessageHandler import MessageHandler


class KeepAliveMessageHandler(MessageHandler):

    def handleMessage(self, message):
        return {"type": "keep_alive_ack"}