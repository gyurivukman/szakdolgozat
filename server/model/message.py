from enum import IntEnum


class MessageTypes(IntEnum):
    GET_ACCOUNT_LIST = 0


class NetworkMessageHeader():

    def __init__(self, raw):
        self.raw = raw
        self.messageType = MessageTypes(raw['messageType'])
        self.uuid = raw.get("uuid", None)


class NetworkMessage():

    def __init__(self, raw):
        self.raw = raw
        self.header = NetworkMessageHeader(raw['header'])
        self.data = raw['data']
