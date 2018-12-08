import json

from MessageHandler import MessageHandler
from src.controller.DatabaseAccessObject import DatabaseAccessObject
from src.controller.Encoder import Encoder
from src.controller.DatabaseBuilder import DatabaseBuilder


class AccountUploadMessageHandler(MessageHandler):

    def __init__(self):
        self.__dao = DatabaseAccessObject()
        self.__encoder = Encoder()

    def handleMessage(self, message):
        newAccounts = []
        for accData in message["data"]:
            entity = self.__buildAccountEntity(accData)
            newAccounts.append(entity)
        self.__dao.insertAccounts(newAccounts)

        dbBuilder = DatabaseBuilder()
        dbBuilder.initDatabase()

        return {"type": "ack"}

    def __buildAccountEntity(self, account):
        entity = {
            "name": self.__encoder.encryptAccountValue(unicode(account["display_name"])),
            "account_type": self.__encoder.encryptAccountValue(unicode(account["account_type"]))
        }
        fields = []
        values = []

        for k, v in account["fields"].iteritems():
            fields.append(k)
            values.append(v)

        entity["structure"] = self.__encoder.encryptAccountValue(json.dumps(fields))
        entity["structure_values"] = self.__encoder.encryptAccountValue(json.dumps(values))

        return entity
