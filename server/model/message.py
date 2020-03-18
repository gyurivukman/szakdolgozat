from enum import IntEnum


class MessageTypes(IntEnum):
    GET_ACCOUNT_LIST = 0


class NetworkMessageHeader():

    def __init__(self, raw):
        self.raw = raw
        messageType = raw.get('messageType', None)
        self.messageType = MessageTypes(messageType) if messageType else None
        self.uuid = raw.get("uuid", None)


class NetworkMessage():

    def __init__(self, raw):
        self.raw = raw
        self.header = NetworkMessageHeader(raw['header'])
        self.data = raw['data']
