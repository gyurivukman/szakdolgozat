from enum import IntEnum
from dataclasses import dataclass


@dataclass
class Task():
    taskType: int
    stale: bool = False
    state: str = None
    uuid: str = None
    data: dict = None
