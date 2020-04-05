from dataclasses import dataclass


@dataclass
class FileData:
    filename: str
    modified: int
    size: int
    path: str = None

    def serialize(self):
        return {"filename": self.filename, "modified": self.modified, "size": self.size, "path": self.path}