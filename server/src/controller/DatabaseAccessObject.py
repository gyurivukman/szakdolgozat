import os
import sqlite3
import getpass

from src.controller.Encoder import Encoder


class DatabaseAccessObject(object):

    def __init__(self):
        self.__DBNAME = "/home/{}/cryptstorepi/database.db".format(getpass.getuser())
        self.__createDB()
        self.__conn = sqlite3.connect(self.__DBNAME)
        self.__cursor = self.__conn.cursor()
        self.__createAccountsTable()

    def __createDB(self):
        dbPath = '/home/{}/cryptstorepi/'.format(getpass.getuser())
        if not os.path.exists(dbPath):
            os.mkdir(dbPath)
            print "Database successfully created!"

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

    def getAccounts(self):
        self.__cursor.execute('SELECT * FROM accounts')
        rows = self.__cursor.fetchall()
        encoder = Encoder()
        accounts = [encoder.decryptAccountEntry(acc) for acc in rows]
        return accounts

    def getAccountsCount(self):
        self.__cursor.execute("SELECT COUNT(*) FROM accounts")
        rawResult = self.__cursor.fetchone()
        return rawResult[0]

    def insertAccounts(self, accounts):
        for account in accounts:
            values = (account["name"], account["account_type"], account["structure"], account["structure_values"])
            self.__cursor.execute('INSERT INTO accounts(name, account_type, structure, structure_values) VALUES(?,?,?,?)', values)
        self.__conn.commit()

    def close(self):
        self.__conn.close()
