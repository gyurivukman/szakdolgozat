

class MessageHandler(object):

    def handleMessage(self, message):
        raise NotImplementedError("method 'handleMessage' not implemented in {}".format(self.__class__))
