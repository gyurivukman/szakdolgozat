from enum import IntEnum
from dataclasses import dataclass


class ConnectionEventTypes(IntEnum):
    CONNECTED = 0
    DISCONNECTED = 1
    HANDSHAKE_SUCCESSFUL = 2
    CONNECTION_ERROR = 3


@dataclass
class ConnectionEvent(object):
    eventType: IntEnum
    data: dict
