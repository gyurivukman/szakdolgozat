import types

from dataclasses import dataclass
from enum import IntEnum



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
    taskType:int
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
