from enum import IntEnum
from uuid import uuid4


class NetworkMessageFormatError(Exception):
    pass


class MessageTypes(IntEnum):
    RESPONSE = 0
    GET_WORKSPACE = 1

    GET_ACCOUNT_LIST = 2
    SET_ACCOUNT_LIST = 3

    SYNC_FILES = 4

    UPLOAD_FILE = 5
    DOWNLOAD_FILE = 6
    MOVE_FILE = 7
    DELETE_FILE = 8

    FILE_STATUS_UPDATE = 9
    FILE_TASK_CANCELLED = 10


class NetworkMessageHeader:

    def __init__(self, raw):
        self.raw = raw
        try:
            if type(raw) != dict:
                raise NetworkMessageFormatError(f"Invalid argument for NetworkMessageHeader: must be dict, received {type(raw)} instead!")
            messageType = MessageTypes(raw['messageType'])
            uuid = raw.get("uuid", None)
            if messageType not in MessageTypes:
                raise NetworkMessageFormatError(f"Unknown value for key 'messageType': {messageType}")
            else:
                self.messageType = messageType
            if uuid:
                if type(uuid) != str:
                    raise NetworkMessageFormatError(f"Invalid header format, key 'uuid' must be of type str. Received {type(uuid)} instead.")
                elif len(uuid) != 32:
                    raise NetworkMessageFormatError(f"Invalid header format, key 'uuid' must be of type str with a length of 32. Received length: {len(uuid)}")
            self.uuid = uuid
        except KeyError:
            raise NetworkMessageFormatError("Invalid header format, missing key: messageType")


class NetworkMessage:

    def __init__(self, raw):
        self.raw = raw
        try:
            if type(raw) != dict:
                raise NetworkMessageFormatError("Invalid network message format! Passed argument must be a dict!")
            self.header = NetworkMessageHeader(raw['header'])
            self.data = raw.get('data', None)
        except KeyError:
            raise NetworkMessageFormatError("Invalid network message format! Passed dict must contain key: 'header'!")

    class Builder:
        __messageType = None
        __uuid = None
        __data = None

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
