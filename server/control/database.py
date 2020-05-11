import sqlite3
import json
import logging
import os


from model.account import AccountTypes, AccountData


module_logger = logging.getLogger(__name__)


class DatabaseAccess():

    def __init__(self):
        self._logger = module_logger.getChild("DatabaseAccess")
        try:
            dbDir = f"{os.path.expanduser('~')}/cryptstorepi_server"
            os.mkdir(dbDir)
            self._logger.debug("Database not found, new created.")
        except FileExistsError:
            self._logger.debug("Database found, skipping creation.")

        dbPath = f"{dbDir}/accounts.db"
        self.__conn = sqlite3.connect(dbPath, check_same_thread=False)
        self.__cursor = self.__conn.cursor()

        self.__cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id int, identifier text, accountType int, cryptoKey text, data text);")

        self.commit()

    def __createAccount(self, accountData):
        self._logger.debug(f"Creating new account with identifier: {accountData.identifier}")
        self.__cursor.execute("SELECT MAX(id) from accounts;")
        highestID = self.__cursor.fetchone()[0]

        newID = highestID + 1 if highestID is not None else 1

        insertCommand = f"INSERT INTO accounts(id, identifier, accountType, cryptoKey, data) VALUES({newID}, '{accountData.identifier}', {accountData.accountType}, '{accountData.cryptoKey}', '{json.dumps(accountData.data)}');"
        self.__cursor.execute(insertCommand)

    def __updateAccount(self, accountData):
        self._logger.debug(f"Updating account with identifier: {accountData.identifier} (ID: {accountData.id})")
        updateCommand = f"UPDATE accounts SET identifier = '{accountData.identifier}', cryptoKey = '{accountData.cryptoKey}', data = '{json.dumps(accountData.data)}' WHERE id = {accountData.id};"
        self.__cursor.execute(updateCommand)

    def getAllAccounts(self):
        self.__cursor.execute("SELECT * FROM accounts;")
        rawAccounts = self.__cursor.fetchall()
        return [AccountData(id=raw[0], identifier=raw[1], accountType=raw[2], cryptoKey=raw[3], data=json.loads(raw[4])) for raw in rawAccounts]

    def createOrUpdateAccount(self, accountData):
        if accountData.id:
            self.__updateAccount(accountData)
        else:
            self.__createAccount(accountData)

    def deleteAccount(self, id):
        self.__cursor.execute(f"DELETE FROM accounts WHERE id={id}")

    def commit(self):
        self.__conn.commit()

    def close(self):
        self.__isConnected = False
        self._logger.debug("Closing database connection.")
        self.__conn.close()
