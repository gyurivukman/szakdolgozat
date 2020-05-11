import unittest

from unittest.mock import patch, MagicMock
from uuid import uuid4

from control.message import *
from model.account import AccountData, AccountTypes
from model.task import Task
from model.message import MessageTypes


class TestGetAccountsListHandler(unittest.TestCase):

    @patch("control.database.DatabaseAccess")
    def setUp(self, fakeDB):
        self.fakeDB = fakeDB
        self.testHandler = GetAccountsListHandler(fakeDB)

    @patch.object(MessageDispatcher, "dispatchResponse")
    def test_handler_retrieves_accounts_from_database_and_sends_response(self, dispatchResponseMock):
        testAccounts = [AccountData(id=1, identifier="testAccountID", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken"})]
        testTask = Task(taskType=MessageTypes.GET_ACCOUNT_LIST, uuid=uuid4().hex)

        self.fakeDB.getAllAccounts.return_value = testAccounts

        self.testHandler.setTask(testTask)
        self.testHandler.handle()

        self.assertEqual(self.fakeDB.getAllAccounts.call_count, 1)

        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.uuid, testTask.uuid)

        self.assertEqual(type(dispatchResponseMock.call_args[0][0].data["accounts"]), list)
        self.assertEqual(len(dispatchResponseMock.call_args[0][0].data["accounts"]), len(testAccounts))

        self.assertEqual(dispatchResponseMock.call_args[0][0].data["accounts"][0], testAccounts[0].serialize())


class TestSetAccountListHandler(unittest.TestCase):

    @patch("control.database.DatabaseAccess")
    def setUp(self, fakeDB):
        self.fakeDB = fakeDB
        self.testHandler = SetAccountListHandler(fakeDB)

    @patch.object(MessageDispatcher, "dispatchResponse")
    def test_set_account_list_handler_sets_accounts_and_returns_response(self, dispatchResponseMock):
        testAccounts = {"accounts": [AccountData(id=1, identifier="testAccountID", accountType=AccountTypes.Dropbox, cryptoKey="sixteen byte key", data={"apiToken": "testApitoken"}).serialize()]}
        testTask = Task(taskType=MessageTypes.SET_ACCOUNT_LIST, uuid=uuid4().hex, data=testAccounts)

        self.testHandler.setTask(testTask)
        self.testHandler.handle()

        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_count, 1)
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].id, testAccounts["accounts"][0]["id"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].identifier, testAccounts["accounts"][0]["identifier"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].accountType, testAccounts["accounts"][0]["accountType"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].cryptoKey, testAccounts["accounts"][0]["cryptoKey"])
        self.assertEqual(self.fakeDB.createOrUpdateAccount.call_args[0][0].data, testAccounts["accounts"][0]["data"])

        self.assertEqual(dispatchResponseMock.call_count, 1)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.messageType, MessageTypes.RESPONSE)
        self.assertEqual(dispatchResponseMock.call_args[0][0].header.uuid, testTask.uuid)
