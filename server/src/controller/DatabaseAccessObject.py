import sqlite3
from src.controller.Encoder import Encoder


class DatabaseAccessObject(object):
    __DBNAME = "database.db"

    def __init__(self):
        self.__conn = sqlite3.connect(self.__DBNAME)
        self.__cursor = self.__conn.cursor()
        self.__createAccountsTable()
        self.__createFilesTable()

    def __createAccountsTable(self):
        self.__cursor.execute(
            '''CREATE TABLE IF NOT EXISTS accounts (
                id integer PRIMARY KEY,
                account_type text NOT NULL,
                name text NOT NULL UNIQUE,
                structure text NOT NULL,
                structure_values text NOT NULL
            )'''
        )
        self.__conn.commit()

    def __createFilesTable(self):
        self.__cursor.execute(
            '''CREATE TABLE IF NOT EXISTS files (
                id integer PRIMARY KEY,
                name text NOT NULL,
                directory text NOT NULL,
                size integer NOT NULL,
                last_modified integer NOT NULL
            )'''
        )
        self.__conn.commit()

    def getFileStatus(self, directory, fileName):
        self.__cursor.execute('SELECT * FROM files WHERE directory=? AND name=?', directory, fileName)
        rawResult = self.__cursor.fetchone()
        #TODO

    def getAccounts(self):
        self.__cursor.execute('SELECT * FROM accounts')
        rows = self.__cursor.fetchall()
        encoder = Encoder()
        accounts = [encoder.decryptAccountEntry(acc) for acc in rows]
        return accounts

    def getAllFiles(self):
        self.__cursor.execute('SELECT * FROM files')
        rawResult = self.__cursor.fetchall()
        return rawResult

    def getAccountsCount(self):
        self.__cursor.execute("SELECT COUNT(*) FROM accounts")
        rawResult = self.__cursor.fetchone()
        return rawResult[0]

    def getFilesCount(self):
        self.__cursor.execute("SELECT COUNT(*) FROM files")
        rawResult = self.__cursor.fetchone()
        return rawResult[0]

    def insertAccounts(self, accounts):
        for account in accounts:
            values = (account["name"], account["account_type"], account["structure"], account["structure_values"])
            self.__cursor.execute('INSERT INTO accounts(name, account_type, structure, structure_values) VALUES(?,?,?,?)', values)
        self.__conn.commit()

    def insertFile(self, newFile):
        values = (newFile["fileName"], newFile["dir"], newFile["size"], newFile["lastModified"])
        self.__cursor.execute('INSERT INTO files(name, directory, size, last_modified) VALUES(?,?,?,?)', values)
        self.__conn.commit()

    def close(self):
        self.__conn.close()