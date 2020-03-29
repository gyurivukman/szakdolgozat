import types

from dataclasses import dataclass
from enum import IntEnum
from typing import List


class AccountTypes(IntEnum):
    Dropbox = 0
    GoogleDrive = 1


class TaskPriorities(IntEnum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


class TaskTypes(IntEnum):
    GET_ACCOUNTS = 0


@dataclass(order=True)
class Task:
    priority: int
    taskType: int
    data: dict = None
    success: types.FunctionType = None
    error: types.FunctionType = None


@dataclass
class AccountData:
    accountType: int
    identifier: str
    cryptoKey: str
    data: dict
    id: int = None

    def toJson(self):
        return {'accountType': self.accountType, 'identifier': self.identifier, 'cryptoKey': self.cryptoKey, 'data': self.data, 'id': self.id}


@dataclass
class ServerConfig:
    address: str
    port: str
    encryptionKey: str


@dataclass
class SshConfig:
    username: str
    password: str


@dataclass
class NetworkConfig:
    remote: ServerConfig
    ssh: SshConfig
    syncDir: str


@dataclass
class FirstStartConfig:
    network: NetworkConfig
    accounts: List[AccountData]
