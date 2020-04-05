from dataclasses import dataclass, field


@dataclass
class FileData:
    filename: str
    modified: int
    size: int
    path: str
    fullPath: str = field(init=False)

    def serialize(self):
        return {"filename": self.filename, "modified": self.modified, "size": self.size, "path": self.path}

    def __post_init__(self):
        self.fullPath = f"{self.path}{self.filename}"
