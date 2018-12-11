from watchdog.events import FileSystemEventHandler, DirModifiedEvent
from PyQt4 import QtCore


class FileEventBroker(FileSystemEventHandler, QtCore.QObject):
    fileEventChannel = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super(FileEventBroker, self).__init__(*args, **kwargs)

    def dispatch(self, event):
        if not isinstance(event, DirModifiedEvent):
            self.fileEventChannel.emit(event)