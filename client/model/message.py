from enum import IntEnum


class MessageTypes(IntEnum):
    RESPONSE = 0
    GET_ACCOUNT_LIST = 1
    SET_ACCOUNT_LIST = 2
    SYNC_FILES = 3


# TODO refaktor.
class NetworkMessageHeader():

    def __init__(self, raw):
        self.raw = raw
        self.messageType = MessageTypes(raw['messageType'])
        self.uuid = raw.get("uuid", None)


class NetworkMessage():

    def __init__(self, raw):
        self.raw = raw
        self.header = NetworkMessageHeader(raw['header'])
        self.data = raw.get('data', None)
