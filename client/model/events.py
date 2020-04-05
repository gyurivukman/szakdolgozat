from enum import IntEnum
from dataclasses import dataclass


class ConnectionEventTypes(IntEnum):
    NETWORK_CONNECTED = 0
    NETWORK_DISCONNECTED = 1
    NETWORK_HANDSHAKE_SUCCESSFUL = 2
    NETWORK_CONNECTION_ERROR = 3

    SSH_CONNECTED = 4
    SSH_DISCONNECTED = 5
    SSH_CONNECTION_ERROR = 6


@dataclass
class ConnectionEvent(object):
    eventType: IntEnum
    data: dict
