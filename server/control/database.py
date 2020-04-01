import sqlite3
import json

from os import mkdir, unlink
from os.path import expanduser

from .abstract import Singleton
from model.account import AccountTypes, AccountData


class DatabaseAccess(metaclass=Singleton):

    def __init__(self):
        try:
            dbDir = f"{expanduser('~')}/cryptstorepi_server"
            mkdir(dbDir)
        except FileExistsError:
            #temporary, should be a pass.
            unlink(f"{expanduser('~')}/cryptstorepi_server/accounts.db")

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

    def __del__(self):
        self.__conn.close()
