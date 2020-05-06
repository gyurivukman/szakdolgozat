import unittest
import logging
import os

from unittest import mock
from queue import Queue, Empty
from dataclasses import dataclass
from collections import namedtuple

from services.files import FileSynchronizer, EnqueueAnyNonHiddenFileEventEventHandler
from model.file import FileData, FileStatuses, FileEventTypes

logging.disable(logging.CRITICAL)

# *******************************************************************
# ****       Event handler tests and dependant fake classes      ****
# *******************************************************************


@dataclass
class MockFileEvent():
    src_path: str
    is_directory: bool


class EnqueueAnyNonHiddenFileEventEventHandlerTests(unittest.TestCase):

    def setUp(self):
        self.queue = Queue()
        self.testHandler = EnqueueAnyNonHiddenFileEventEventHandler(self.queue)

    def test_file_event_is_enqueued(self):
        testEvent = MockFileEvent("testSrcPath", False)
        self.testHandler.on_any_event(testEvent)

        enqueuedEvent = self.queue.get_nowait()

        self.assertEqual(testEvent.src_path, enqueuedEvent.src_path)
        self.assertEqual(enqueuedEvent.is_directory, False)

    def test_directory_event_is_ignored(self):
        testEvent = MockFileEvent("testSrcPath", True)
        self.testHandler.on_any_event(testEvent)

        try:
            self.queue.get_nowait()
            self.fail("A directory event didn't get ignored in EnqueueAnyNonHiddenFileEventEventHandler!")
        except Empty:
            pass

    def test_hidden_file_event_is_ignored_simple_path(self):
        testEvent = MockFileEvent(".hiddenFile", False)
        self.testHandler.on_any_event(testEvent)

        try:
            self.queue.get_nowait()
            self.fail(f"A hidden file event didn't get ignored in EnqueueAnyNonHiddenFileEventEventHandler! src_path was: {testEvent.src_path}")
        except Empty:
            pass

    def test_hidden_file_event_is_ignored_if_src_path_is_complex(self):
        testEvent = MockFileEvent("someSubdir/someOtherSubdir/.hiddenFile", False)
        self.testHandler.on_any_event(testEvent)

        try:
            self.queue.get_nowait()
            self.fail(f"A hidden file event didn't get ignored in EnqueueAnyNonHiddenFileEventEventHandler! src_path was: {testEvent.src_path}")
        except Empty:
            pass


# *******************************************************************
# ****       File Syncer tests and dependant fake classes        ****
# *******************************************************************


class MockStatusEventReceiver():

    def __init__(self, syncer):
        self.syncer = syncer
        self.syncer.fileTaskChannel.connect(self.__onFileTask)
        self.syncer.fileStatusChannel.connect(self.__onFileStatus)
        self.events = []
        self.tasks = []

    def __onFileStatus(self, event):
        self.events.append(event)

    def __onFileTask(self, task):
        self.tasks.append(task)


@dataclass
class MockFileSystemEntry():
    path: str
    isDir: bool
    st_mtime: int
    st_size: int

    def is_dir(self, follow_symlinks):
        return self.isDir

    def stat(self):
        return self


class FileSynchronizerTests(unittest.TestCase):

    def setUp(self):
        self.testSyncDir = "/testSyncDir"
        self.syncer = FileSynchronizer(self.testSyncDir)
        self.fakeEventReceiver = MockStatusEventReceiver(self.syncer)

    @mock.patch('os.unlink')
    @mock.patch('os.scandir')
    def test_sync_files(self, scandirMock, osUnlinkMock):
        fakeLocalFiles = [
            MockFileSystemEntry(self.__generateFullPath("existsLocalOnlySimplePath"), False, 5, 5),
            MockFileSystemEntry(self.__generateFullPath(".hiddenShouldBeDeleted"), False, 5, 5),
            MockFileSystemEntry(self.__generateFullPath("existsBothLocalNewer"), False, 6, 5),
            MockFileSystemEntry(self.__generateFullPath("existsBothRemoteNewer"), False, 4, 5),
        ]

        fakeRemoteFiles = [
            FileData(filename="existsRemoteOnlySimplePath", modified=5, size=5, path="", fullPath="existsOnlyRemoteSimplePath"),
            FileData(filename="existsBothLocalNewer", modified=5, size=5, path="", fullPath="existsBothLocalNewer"),
            FileData(filename="existsBothRemoteNewer", modified=6, size=5, path="", fullPath="existsBothRemoteNewer")
        ]
        scandirMock.return_value = iter(fakeLocalFiles)
        expectedFileResult = [fakeLocalFiles[0], fakeLocalFiles[2], fakeRemoteFiles[2], fakeRemoteFiles[0]]

        self.syncer.syncFileList(fakeRemoteFiles)

        self.assertEqual(len(expectedFileResult), len(self.fakeEventReceiver.events))

        for i in range(len(expectedFileResult)):
            if type(expectedFileResult[i]) == MockFileSystemEntry:
                comparablePath = expectedFileResult[i].path.replace(f"{self.testSyncDir}/", "")
                # Compare events
                self.assertEqual(self.fakeEventReceiver.events[i].eventType, FileEventTypes.CREATED)
                self.assertEqual(comparablePath, self.fakeEventReceiver.events[i].sourcePath)
                self.assertEqual(expectedFileResult[i].st_mtime, self.fakeEventReceiver.tasks[i].subject.modified)
                # Compare taskdata
                self.assertEqual(expectedFileResult[i].st_size, self.fakeEventReceiver.tasks[i].subject.size)
            else:
                # compare event
                self.assertEqual(expectedFileResult[i].fullPath, self.fakeEventReceiver.events[i].sourcePath)
                # compare taskData
                self.assertEqual(expectedFileResult[i].size, self.fakeEventReceiver.tasks[i].subject.size)

        self.assertEqual(self.fakeEventReceiver.events[0].status, FileStatuses.UPLOADING_FROM_LOCAL)
        self.assertEqual(self.fakeEventReceiver.events[1].status, FileStatuses.UPLOADING_FROM_LOCAL)
        self.assertEqual(self.fakeEventReceiver.events[2].status, FileStatuses.DOWNLOADING_FROM_CLOUD)
        self.assertEqual(self.fakeEventReceiver.events[3].status, FileStatuses.DOWNLOADING_FROM_CLOUD)

    def __generateFullPath(self, filePath):
        return f"{self.testSyncDir}/{filePath}"


if __name__ == '__main__':
    unittest.main()
