import unittest
import json

from unittest.mock import patch, MagicMock

from control.database import DatabaseAccess
from model.account import AccountData, AccountTypes


class TestDatabase(unittest.TestCase):

    @patch("sqlite3.connect")
    @patch("os.mkdir")
    @patch("os.path.expanduser")
    def test_dbAccess_creates_server_dir_in_user_home_and_creates_db_file_and_creates_accounts_table_if_doesnt_exist(self, expanduserMock, mkdirMock, sqlite3_connectMock):
        expanduserMock.return_value = "/home/testUser"
        fakeConnection = MagicMock()
        fakeCursor = MagicMock()

        sqlite3_connectMock.return_value = fakeConnection
        sqlite3_connectMock.return_value.cursor.return_value = fakeCursor

        dbAccess = DatabaseAccess()

        self.assertEqual(sqlite3_connectMock.call_count, 1)
        self.assertEqual(sqlite3_connectMock.call_args[0][0], "/home/testUser/cryptstorepi_server/accounts.db")

        self.assertEqual(fakeConnection.cursor.call_count, 1)
        self.assertEqual(fakeCursor.execute.call_count, 1)
        self.assertEqual(fakeCursor.execute.call_args[0][0], "CREATE TABLE IF NOT EXISTS accounts (id int, identifier text, accountType int, cryptoKey text, data text);")
        self.assertEqual(fakeConnection.commit.call_count, 1)

    @patch("sqlite3.connect")
    @patch("os.mkdir")
    @patch("os.path.expanduser")
    def test_db_access_retrieves_accounts(self, expanduserMock, mkdirMock, sqlite3_connectMock):
        fakeAccData1 = {"fakeAccData1": "fakeValue1"}
        fakeAccData2 = {"fakeAccData2": "fakeValue2"}

        testAccountInDBData = [
            (0, "testID1", 0, "CryptoKey1111111", json.dumps(fakeAccData1)),
            (1, "testID2", 1, "CryptoKey2222222", json.dumps(fakeAccData2))
        ]

        expanduserMock.return_value = "/home/testUser"
        fakeConnection = MagicMock()
        fakeCursor = MagicMock()

        sqlite3_connectMock.return_value = fakeConnection
        sqlite3_connectMock.return_value.cursor.return_value = fakeCursor
        fakeCursor.fetchall.return_value = testAccountInDBData

        dbAccess = DatabaseAccess()
        dbAccounts = dbAccess.getAllAccounts()

        self.assertEqual(fakeCursor.execute.call_count, 2)
        self.assertEqual(fakeCursor.execute.call_args[0][0], "SELECT * FROM accounts;")

        self.assertEqual(type(dbAccounts[0]), AccountData)
        self.assertEqual(dbAccounts[0].id, testAccountInDBData[0][0])
        self.assertEqual(dbAccounts[0].identifier, testAccountInDBData[0][1])
        self.assertEqual(dbAccounts[0].accountType, testAccountInDBData[0][2])
        self.assertEqual(dbAccounts[0].cryptoKey, testAccountInDBData[0][3])
        self.assertEqual(dbAccounts[0].data, fakeAccData1)

        self.assertEqual(type(dbAccounts[1]), AccountData)
        self.assertEqual(dbAccounts[1].id, testAccountInDBData[1][0])
        self.assertEqual(dbAccounts[1].identifier, testAccountInDBData[1][1])
        self.assertEqual(dbAccounts[1].accountType, testAccountInDBData[1][2])
        self.assertEqual(dbAccounts[1].cryptoKey, testAccountInDBData[1][3])
        self.assertEqual(dbAccounts[1].data, fakeAccData2)

    @patch("sqlite3.connect")
    @patch("os.mkdir")
    @patch("os.path.expanduser")
    def test_db_access_creates_or_updates_accounts(self, expanduserMock, mkdirMock, sqlite3_connectMock):
        testAccountData = [
            AccountData(AccountTypes.Dropbox, "testAccount1", "testCryptoKey1", {"apiToken": "testApiToken1"}),
            AccountData(AccountTypes.Dropbox, "testAccount2", "testCryptoKey2", {"apiToken": "testApiToken2"}, 1)
        ]

        fakeConnection = MagicMock()
        fakeCursor = MagicMock()

        sqlite3_connectMock.return_value = fakeConnection
        sqlite3_connectMock.return_value.cursor.return_value = fakeCursor

        fakeCursor.fetchone.return_value = [1]

        db = DatabaseAccess()
        db.createOrUpdateAccount(testAccountData[0])
        db.createOrUpdateAccount(testAccountData[1])

        self.assertEqual(fakeCursor.execute.call_count, 4)
        self.assertEqual(fakeCursor.execute.call_args_list[1][0][0], "SELECT MAX(id) from accounts;")

        insertCommand = f"INSERT INTO accounts(id, identifier, accountType, cryptoKey, data) VALUES(2, '{testAccountData[0].identifier}', {testAccountData[0].accountType}, '{testAccountData[0].cryptoKey}', '{json.dumps(testAccountData[0].data)}');"
        self.assertEqual(fakeCursor.execute.call_args_list[2][0][0], insertCommand)

        updateCommand = f"UPDATE accounts SET identifier = '{testAccountData[1].identifier}', cryptoKey = '{testAccountData[1].cryptoKey}', data = '{json.dumps(testAccountData[1].data)}' WHERE id = 1;"
        self.assertEqual(fakeCursor.execute.call_args_list[3][0][0], updateCommand)

        self.assertEqual(fakeConnection.commit.call_count, 3)

    @patch("sqlite3.connect")
    @patch("os.mkdir")
    @patch("os.path.expanduser")
    def test_db_access_closes_connection(self, expanduserMock, mkdirMock, sqlite3_connectMock):
        fakeConnection = MagicMock()
        fakeCursor = MagicMock()

        sqlite3_connectMock.return_value = fakeConnection
        sqlite3_connectMock.return_value.cursor.return_value = fakeCursor

        db = DatabaseAccess()
        db.close()

        self.assertEqual(fakeConnection.close.call_count, 1)

    @patch("sqlite3.connect")
    @patch("os.mkdir")
    @patch("os.path.expanduser")
    def test_db_access_commits_to_connection(self, expanduserMock, mkdirMock, sqlite3_connectMock):
        fakeConnection = MagicMock()
        fakeCursor = MagicMock()

        sqlite3_connectMock.return_value = fakeConnection
        sqlite3_connectMock.return_value.cursor.return_value = fakeCursor

        db = DatabaseAccess()
        db.commit()

        self.assertEqual(fakeConnection.commit.call_count, 2)