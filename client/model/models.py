from dataclasses import dataclass
from enum import IntEnum


class AccountTypes(IntEnum):
    Dropbox = 0
    GoogleDrive = 1


@dataclass
class AccountData():
    accountType: int
    data: dict
    id: int = None
