import unittest

from unittest.mock import patch, MagicMock
from queue import Empty

from control.message import MessageDispatcher
from model.message import NetworkMessage, MessageTypes
from model.task import TaskArchive


class MessageDispatcherTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dispatcher = MessageDispatcher()
        cls.taskArchive = TaskArchive()

    def setUp(self):
        self.taskArchive.clearAllTasks()

    def test_incoming_get_workspace_message_is_instant(self):
        testMessage = NetworkMessage.Builder(MessageTypes.GET_WORKSPACE).withRandomUUID().build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("GET_WORKSPACE message got queued to the long task queue 'incoming_task_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("GET_WORKSPACE message got queued to the outgoing task queue 'outgoing_message_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.assertEqual(task.taskType, testMessage.header.messageType)
        except Empty:
            self.fail("GET_WORKSPACE message was not queued to the incoming instant task queue 'incoming_instant_task_queue'! Should be an instant task on the incoming_instant_task_queue!")

    def test_incoming_get_accountlist_message_is_instant(self):
        testMessage = NetworkMessage.Builder(MessageTypes.GET_ACCOUNT_LIST).withRandomUUID().build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("GET_ACCOUNT_LIST message got queued to the long task queue 'incoming_task_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("GET_ACCOUNT_LIST message got queued to the outgoing task queue 'outgoing_message_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.assertEqual(task.taskType, testMessage.header.messageType)
        except Empty:
            self.fail("GET_ACCOUNT_LIST message was not queued to the incoming instant task queue 'incoming_instant_task_queue'! Should be an instant task on the incoming_instant_task_queue!")

    def test_incoming_set_accountlist_message_is_instant(self):
        testMessage = NetworkMessage.Builder(MessageTypes.SET_ACCOUNT_LIST).withRandomUUID().build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("SET_ACCOUNT_LIST message got queued to the long task queue 'incoming_task_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("SET_ACCOUNT_LIST message got queued to the outgoing task queue 'outgoing_message_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.assertEqual(task.taskType, testMessage.header.messageType)
        except Empty:
            self.fail("SET_ACCOUNT_LIST message was not queued to the incoming instant task queue 'incoming_instant_task_queue'! Should be an instant task on the incoming_instant_task_queue!")

    def test_incoming_sync_files_message_is_instant(self):
        testMessage = NetworkMessage.Builder(MessageTypes.SYNC_FILES).withRandomUUID().build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("SYNC_FILES message got queued to the long task queue 'incoming_task_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("SYNC_FILES message got queued to the outgoing task queue 'outgoing_message_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.assertEqual(task.taskType, testMessage.header.messageType)
        except Empty:
            self.fail("SYNC_FILES message was not queued to the incoming instant task queue 'incoming_instant_task_queue'! Should be an instant task on the incoming_instant_task_queue!")

    @patch.object(TaskArchive, "removeTask")
    @patch.object(TaskArchive, "cancelTask")
    def test_incoming_move_file_message_is_instant_and_stops_and_removes_related_file_tasks(self, cancelTaskMock, removeTaskMock):
        testData = {"source": "testSourcePath", "target": {"fullPath": "testTargetPath"}}
        testMessage = NetworkMessage.Builder(MessageTypes.MOVE_FILE).withRandomUUID().withData(testData).build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("MOVE_FILE message got queued to the long task queue 'incoming_task_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("MOVE_FILE message got queued to the outgoing task queue 'outgoing_message_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.assertEqual(task.taskType, testMessage.header.messageType)
        except Empty:
            self.fail("MOVE_FILE message was not queued to the incoming instant task queue 'incoming_instant_task_queue'! Should be an instant task on the incoming_instant_task_queue!")

        removeTaskMock
        self.assertEqual(cancelTaskMock.call_count, 2)
        self.assertEqual(cancelTaskMock.call_args_list[0][0][0], testData["source"])
        self.assertEqual(cancelTaskMock.call_args_list[1][0][0], testData["target"]["fullPath"])

        self.assertEqual(removeTaskMock.call_count, 2)
        self.assertEqual(removeTaskMock.call_args_list[0][0][0], testData["source"])
        self.assertEqual(removeTaskMock.call_args_list[1][0][0], testData["target"]["fullPath"])

    @patch.object(TaskArchive, "removeTask")
    @patch.object(TaskArchive, "cancelTask")
    def test_incoming_delete_file_message_is_instant_and_stops_and_removes_related_file_tasks(self, cancelTaskMock, removeTaskMock):
        testData = {"fullPath": "testDeleteFile"}
        testMessage = NetworkMessage.Builder(MessageTypes.DELETE_FILE).withRandomUUID().withData(testData).build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("DELETE_FILE message got queued to the long task queue 'incoming_task_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("DELETE_FILE message got queued to the outgoing task queue 'outgoing_message_queue'! Should be an instant task on the incoming_instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.assertEqual(task.taskType, testMessage.header.messageType)
        except Empty:
            self.fail("DELETE_FILE message was not queued to the incoming instant task queue 'incoming_instant_task_queue'! Should be an instant task on the incoming_instant_task_queue!")

        self.assertEqual(cancelTaskMock.call_count, 1)
        self.assertEqual(cancelTaskMock.call_args[0][0], testData["fullPath"])
        self.assertEqual(removeTaskMock.call_count, 1)
        self.assertEqual(removeTaskMock.call_args[0][0], testData["fullPath"])

    @patch.object(TaskArchive, "removeTask")
    @patch.object(TaskArchive, "cancelTask")
    def test_incoming_delete_file_message_is_instant_but_not_queued_and_stops_and_removes_related_file_tasks(self, cancelTaskMock, removeTaskMock):
        testData = {"fullPath": "testCancelledFilePath"}
        testMessage = NetworkMessage.Builder(MessageTypes.FILE_TASK_CANCELLED).withRandomUUID().withData(testData).build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("FILE_TASK_CANCELLED message got queued to the instant task queue 'incoming_instant_task_queue'! Should be an instant task handled by the dispatcher.")
        except Empty:
            pass

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("FILE_TASK_CANCELLED message got queued to the long task queue 'incoming_task_queue'! Should be an instant task handled by the dispatcher.")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("FILE_TASK_CANCELLED message got queued to the outgoing task queue 'outgoing_message_queue'! Should be an instant task handled by the dispatcher.")
        except Empty:
            pass

        self.assertEqual(cancelTaskMock.call_count, 1)
        self.assertEqual(cancelTaskMock.call_args[0][0], testData["fullPath"])
        self.assertEqual(removeTaskMock.call_count, 1)
        self.assertEqual(removeTaskMock.call_args[0][0], testData["fullPath"])

    def test_dispatch_response_enqueues_message_to_outgoing_queue(self):
        testMessage = NetworkMessage.Builder(MessageTypes.RESPONSE).withRandomUUID().build()

        self.dispatcher.dispatchResponse(testMessage)

        try:
            self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()
            self.fail("Response message got queued to the incoming_task_queue! Should be sent to the outgoing_message_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.fail("Response message got queued to the incoming_instant_task_queue! Should be sent to the outgoing_message_queue!")
        except Empty:
            pass

        try:
            message = self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
        except Empty:
            self.fail("Response message did not get queued to the incoming_instant_task_queue! Should be sent to the outgoing_message_queue!")

    @patch.object(TaskArchive, "addTask")
    def test_incoming_upload_file_is_a_long_task_and_is_added_to_the_task_archive(self, addTaskMock):
        testData = {"fullPath": "testFullPath"}
        testMessage = NetworkMessage.Builder(MessageTypes.UPLOAD_FILE).withRandomUUID().withData(testData).build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.fail("UPLOAD_FILE message got queued to the incoming_instant_task_queue! Should be sent to the instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("UPLOAD_FILE message got queued to the outgoing_message_queue! Should be sent to the instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()

            self.assertEqual(task.data["fullPath"], testData["fullPath"])
        except Empty:
            self.fail("UPLOAD_FILE message was not queued to the incoming_task_queue! Should be sent to the incoming_task_queue!")

        self.assertEqual(addTaskMock.call_count, 1)
        self.assertEqual(addTaskMock.call_args[0][0], testData["fullPath"])

    @patch.object(TaskArchive, "addTask")
    def test_incoming_download_file_is_a_long_task_and_is_added_to_the_task_archive(self, addTaskMock):
        testData = {"fullPath": "testFullPath"}
        testMessage = NetworkMessage.Builder(MessageTypes.UPLOAD_FILE).withRandomUUID().withData(testData).build()

        self.dispatcher.dispatchIncomingMessage(testMessage)

        try:
            self.dispatcher.incoming_instant_task_queue.get_nowait()
            self.dispatcher.incoming_instant_task_queue.task_done()
            self.fail("DOWNLOAD_FILE message got queued to the incoming_instant_task_queue! Should be sent to the instant_task_queue!")
        except Empty:
            pass

        try:
            self.dispatcher.outgoing_message_queue.get_nowait()
            self.dispatcher.outgoing_message_queue.task_done()
            self.fail("DOWNLOAD_FILE message got queued to the outgoing_message_queue! Should be sent to the instant_task_queue!")
        except Empty:
            pass

        try:
            task = self.dispatcher.incoming_task_queue.get_nowait()
            self.dispatcher.incoming_task_queue.task_done()

            self.assertEqual(task.data["fullPath"], testData["fullPath"])
        except Empty:
            self.fail("DOWNLOAD_FILE message was not queued to the incoming_task_queue! Should be sent to the incoming_task_queue!")

        self.assertEqual(addTaskMock.call_count, 1)
        self.assertEqual(addTaskMock.call_args[0][0], testData["fullPath"])
