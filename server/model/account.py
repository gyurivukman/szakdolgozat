from enum import IntEnum
from dataclasses import dataclass


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
        return {
            "id": self.id,
            "accountType": self.accountType,
            "identifier": self.identifier,
            "cryptoKey": self.cryptoKey,
            "data": self.data
        }
