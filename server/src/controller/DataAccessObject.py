import sqlite3


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
        rawResult = self.__cursor.fetchall()
        #TODO

    def insertAccounts(self, accountData):
        pass
        #TODO

    def close(self):
        self.__conn.close()