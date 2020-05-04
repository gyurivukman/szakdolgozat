import types

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Callable


class AccountTypes(IntEnum):
    Dropbox = 0
    GoogleDrive = 1


@dataclass
class AccountData:
    accountType: AccountTypes
    identifier: str
    cryptoKey: str
    data: dict
    id: int = None

    def serialize(self):
        return {'id': self.id, 'accountType': self.accountType, 'identifier': self.identifier, 'cryptoKey': self.cryptoKey, 'data': self.data}


@dataclass
class AccountSavedEvent:
    accountData: AccountData
    callBack: Callable


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
