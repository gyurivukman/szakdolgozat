import sqlite3
import json
import logging

from os import mkdir, unlink
from os.path import expanduser

from .abstract import Singleton
from model.account import AccountTypes, AccountData


module_logger = logging.getLogger(__name__)


class DatabaseAccess(metaclass=Singleton):

    def __init__(self):
        self._logger = module_logger.getChild("DatabaseAccess")
        try:
            dbDir = f"{expanduser('~')}/cryptstorepi_server"
            mkdir(dbDir)
            self._logger.debug("Database not found, new created.")
        except FileExistsError:
            self._logger.debug("Database found, skipping creation.")

        dbPath = f"{dbDir}/accounts.db"
        self.__conn = sqlite3.connect(dbPath)
        self.__cursor = self.__conn.cursor()

        self.__cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id int, identifier text, type int, cryptoKey text, data text);")
        # data = json.dumps({"apiToken": "myCuteLittleApiKey"})
        # self.__cursor.execute(f"INSERT INTO accounts(id, identifier, type, cryptoKey, data) VALUES (1, 'droppy', 0, 'sixteen byte key', '{json.dumps(data)}');")

        self.__conn.commit()

    def getAllAccounts(self):
        self.__cursor.execute("SELECT * FROM accounts;")
        rawAccounts = self.__cursor.fetchall()
        return [AccountData(id=raw[0], identifier=raw[1], accountType=raw[2], cryptoKey=raw[3], data=json.loads(raw[4])) for raw in rawAccounts]

    def close(self):
        self._logger.debug("Closing database connection.")
        self.__conn.close()
