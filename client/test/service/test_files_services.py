import unittest
import logging
import os

from unittest import mock
from queue import Queue, Empty
from dataclasses import dataclass
from collections import namedtuple

from services.files import FileSynchronizer, EnqueueAnyNonHiddenFileEventEventHandler
from model.file import FileData, FileStatuses, FileEventTypes
from model.task import FileTask

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

    @mock.patch("time.sleep")
    @mock.patch("shutil.move")
    @mock.patch('os.utime')
    def test_finalize_download_sends_out_synced_event_upon_completion(self, os_utimeMock, shutil_moveMock, time_sleepMock):
        fileData = FileData(filename="testFileName", modified=5, size=10, path="", fullPath="testFileName", status=FileStatuses.DOWNLOADING_TO_LOCAL)
        finalizeTask = FileTask(uuid="testUUID", taskType=FileStatuses.DOWNLOADING_TO_LOCAL, subject=fileData, stale=False)

        self.syncer.finalizeDownload(finalizeTask)

        self.assertEqual(len(self.fakeEventReceiver.events), 1)
        self.assertEqual(self.fakeEventReceiver.events[0].eventType, FileEventTypes.STATUS_CHANGED)
        self.assertEqual(self.fakeEventReceiver.events[0].sourcePath, fileData.fullPath)
        self.assertEqual(self.fakeEventReceiver.events[0].status, FileStatuses.SYNCED)

    @mock.patch("time.sleep")
    @mock.patch("shutil.move")
    @mock.patch('os.utime')
    def test_finalize_download_requires_no_directory_creation(self, os_utimeMock, shutil_moveMock, time_sleepMock):
        fileData = FileData(filename="testFileName", modified=5, size=10, path="", fullPath="testFileName", status=FileStatuses.DOWNLOADING_TO_LOCAL)
        finalizeTask = FileTask(uuid="testUUID", taskType=FileStatuses.DOWNLOADING_TO_LOCAL, subject=fileData, stale=False)

        self.syncer.finalizeDownload(finalizeTask)

        self.assertEqual(os_utimeMock.called, True)
        self.assertEqual(os_utimeMock.call_args[0][0], f"{self.testSyncDir}/.{finalizeTask.uuid}")
        self.assertEqual(os_utimeMock.call_args[0][1], (fileData.modified, fileData.modified))

        self.assertEqual(shutil_moveMock.called, True)
        self.assertEqual(shutil_moveMock.call_args[0][0], f"{self.testSyncDir}/.{finalizeTask.uuid}")
        self.assertEqual(shutil_moveMock.call_args[0][1], f"{self.testSyncDir}/{fileData.fullPath}")

        self.assertEqual(time_sleepMock.called, True)
        self.assertEqual(time_sleepMock.call_args[0][0], 0.5)

    @mock.patch("os.mkdir")
    @mock.patch("time.sleep")
    @mock.patch("shutil.move")
    @mock.patch('os.utime')
    def test_finalize_download_requires_directory_creation(self, os_utimeMock, shutil_moveMock, time_sleepMock, os_mkdirMock):
        fileData = FileData(filename="testFileName", modified=5, size=10, path="subDir/subSubDir", fullPath="subDir/subSubDir/testFileName", status=FileStatuses.DOWNLOADING_TO_LOCAL)
        finalizeTask = FileTask(uuid="testUUID", taskType=FileStatuses.DOWNLOADING_TO_LOCAL, subject=fileData, stale=False)

        shutil_moveMock.side_effect = [FileNotFoundError(), None, None]

        self.syncer.finalizeDownload(finalizeTask)

        self.assertTrue(shutil_moveMock.called)
        self.assertEqual(shutil_moveMock.call_count, 3)

        # First Move fails.
        self.assertEqual(shutil_moveMock.call_args_list[0][0][0], f"{self.testSyncDir}/.{finalizeTask.uuid}")
        self.assertEqual(shutil_moveMock.call_args_list[0][0][1], f"{self.testSyncDir}/{fileData.path}/.{finalizeTask.uuid}")

        # Second Move moves the hidden file to its final place after the directories have been created.
        self.assertEqual(shutil_moveMock.call_args_list[1][0][0], f"{self.testSyncDir}/.{finalizeTask.uuid}")
        self.assertEqual(shutil_moveMock.call_args_list[1][0][1], f"{self.testSyncDir}/{fileData.path}/.{finalizeTask.uuid}")

        # Final move renames the file from a hidden one to its actual file name, already in its final place.
        self.assertEqual(shutil_moveMock.call_args_list[2][0][0], f"{self.testSyncDir}/{fileData.path}/.{finalizeTask.uuid}")
        self.assertEqual(shutil_moveMock.call_args_list[2][0][1], f"{self.testSyncDir}/{fileData.path}/{fileData.filename}")

        self.assertTrue(os_mkdirMock.called)
        self.assertTrue(os_mkdirMock.calle_count, 2)
        self.assertEqual(os_mkdirMock.call_args_list[0][0][0], f"{self.testSyncDir}/subDir")
        self.assertEqual(os_mkdirMock.call_args_list[1][0][0], f"{self.testSyncDir}/subDir/subSubDir")

        self.assertTrue(time_sleepMock.called)
        self.assertEqual(time_sleepMock.call_count, 1)
        self.assertEqual(time_sleepMock.call_args[0][0], 0.5)

    def __generateFullPath(self, filePath):
        return f"{self.testSyncDir}/{filePath}"


if __name__ == '__main__':
    unittest.main()
