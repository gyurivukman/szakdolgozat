from dataclasses import dataclass, field


@dataclass
class FileData:
    filename: str
    modified: int
    size: int
    path: str
    fullPath: str

    def serialize(self):
        return {"filename": self.filename, "modified": self.modified, "size": self.size, "path": self.path, "fullPath": self.fullPath}
