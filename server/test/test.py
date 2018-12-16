import datetime
import unittest
import json
from mock import patch
import sys
import dropbox
from dropbox.files import WriteMode, FileMetadata
import src.model.TaskStatus as TaskStatus
from src.controller.messagehandlers.DeleteFileMessageHandler import DeleteFileMessageHandler
from src.controller.messagehandlers.GetFileListMessageHandler import GetFileListMessageHandler
from src.controller.messagehandlers.MoveFileMessageHandler import MoveFileMessageHandler
from src.controller.messagehandlers.ProgressCheckMessageHandler import ProgressCheckMessageHandler


class TestMessageHandlers(unittest.TestCase):

    @patch.object(dropbox.Dropbox, "files_delete")
    @patch.object(dropbox.Dropbox, "users_get_current_account")
    def test_delete(self, users, filedelete):
        testargs = ["prog", "--encryptionkey", "G+KbPeShVmYq3t6w"]
        with patch.object(sys, 'argv', testargs):
            handler = DeleteFileMessageHandler()
            response = handler.handleMessage({"data": "example.txt"})
            self.assertEquals(response, {"type": "ack"})
            self.assertEquals(filedelete.call_args[0][0], "/example.txt.enc")

    @patch.object(dropbox.Dropbox, "files_list_folder")
    @patch.object(dropbox.Dropbox, "users_get_current_account")
    def test_list_empty(self, users, filelist):
        testargs = ["prog", "--encryptionkey", "G+KbPeShVmYq3t6w"]
        with patch.object(sys, 'argv', testargs):
            handler = GetFileListMessageHandler()
            response = handler.handleMessage({})
            self.assertEquals(response, [])

    @patch.object(dropbox.Dropbox, "files_list_folder")
    @patch.object(dropbox.Dropbox, "users_get_current_account")
    def test_list_simple(self, users, filelist):
        filelist.return_value = ListHelper([FileMetadata(name="/example.txt.enc", path_display="/example.txt.enc", size=50, client_modified=datetime.datetime(2018, 12, 10, 11, 32, 21))])
        testargs = ["prog", "--encryptionkey", "G+KbPeShVmYq3t6w"]
        with patch.object(sys, 'argv', testargs):
            handler = GetFileListMessageHandler()
            response = handler.handleMessage({})
            self.assertEquals(response, [{'fileName': u'/example.txt', 'lastModified': 1544437941, 'path': u'example.txt', 'size': 50}])

    @patch.object(dropbox.Dropbox, "files_move")
    @patch.object(dropbox.Dropbox, "users_get_current_account")
    def test_move(self, users, filemove):
        testargs = ["prog", "--encryptionkey", "G+KbPeShVmYq3t6w"]
        with patch.object(sys, 'argv', testargs):
            handler = MoveFileMessageHandler()
            response = handler.handleMessage({"data": {"from": "example.txt", "to": "example2.txt"}})
            self.assertEquals(response, {"type": "ack"})
            self.assertEquals(filemove.call_args[0][0], "/example.txt.enc")
            self.assertEquals(filemove.call_args[0][1], "/example2.txt.enc")

    def test_progress_check_clean_cache(self):
        cache = {"task1": TaskStatus.SYNCED, "task2": TaskStatus.DOWNLOADING_FROM_CLOUD}
        handler = ProgressCheckMessageHandler(cache)
        response = handler.handleMessage({"data": "task1"})
        self.assertEquals(response, {"status": 10})
        self.assertEquals(cache, {'task2': 6})


class ListHelper:

    def __init__(self, lists):
        self.entries = lists
