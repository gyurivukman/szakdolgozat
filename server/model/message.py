from enum import IntEnum


class MessageTypes(IntEnum):
    RESPONSE = 0
    GET_ACCOUNT_LIST = 1
    SET_ACCOUNT_LIST = 2
    SYNC_FILES = 3


class NetworkMessageHeader():

    def __init__(self, raw):
        self.raw = raw
        self.messageType = MessageTypes(raw["messageType"])
        self.uuid = raw.get("uuid", None)


class NetworkMessage():

    def __init__(self, raw):
        self.raw = raw
        self.header = NetworkMessageHeader(raw["header"])
        self.data = raw.get("data")

    class Builder():
        __messageType = None
        __uuid = None
        __data = {}

        def __init__(self, messageType):
            self.__messageType = messageType

        def withUUID(self, uuid):
            self.__uuid = uuid
            return self

        def withRandomUUID(self):
            self.__uuid = uuid4().hex
            return self

        def withData(self, data):
            self.__data = data
            return self

        def build(self):
            return NetworkMessage({"header": {"messageType": self.__messageType, "uuid": self.__uuid}, "data": self.__data})
