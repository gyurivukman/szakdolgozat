from dataclasses import dataclass
from enum import IntEnum


class AccountTypes(IntEnum):
    Dropbox = 0
    GoogleDrive = 1


class TaskPriorities(IntEnum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


@dataclass(order=True)
class Task:
    priority: int
    data: dict


@dataclass
class AccountData:
    accountType: int
    identifier: str
    cryptoKey: str
    data: dict
    id: int = None
