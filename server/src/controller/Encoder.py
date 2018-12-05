import base64
import json
import itertools 
import sys
import argparse

from Crypto.Cipher import AES


class EncoderWrapper(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(EncoderWrapper, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Encoder(object):
    __metaclass__ = EncoderWrapper

    def __init__(self):
        self.__encryptionKey = self.__findEncryptionKeyInSysArgs()
        self.__paddingChar = " "
        self.__cipher = AES.new(self.__encryptionKey)

    def __findEncryptionKeyInSysArgs(self):
        found = False
        args = sys.argv
        index = 0
        while not found:
            found = args[index] == '--encryptionkey'
            if not found:
                index = index + 1
        return args[index+1]

    def decryptMessage(self, message):
        decryptedMessage = base64.b64decode(message)
        decryptedMessage = self.__cipher.decrypt(decryptedMessage)
        decryptedMessage = self.__removePadding(decryptedMessage)
        print decryptedMessage
        return json.loads(decryptedMessage)

    def __removePadding(self, message):
        return message.rstrip(self.__paddingChar)

    def encryptMessage(self, message):
        message = json.dumps(message)
        paddedMessage = self.__addPadding(message)
        encryptedMessage = self.__cipher.encrypt(paddedMessage)
        return base64.b64encode(encryptedMessage)+";"

    def encryptAccountValue(self, value):
        paddedValue = self.__addPadding(value)
        encryptedValue = self.__cipher.encrypt(paddedValue)
        return base64.b64encode(encryptedValue)

    def decryptAccountEntry(self, entry):
        account = {
            "id": entry[0],
            "account_type": self.__decryptAccountValue(entry[1]),
            "display_name": self.__decryptAccountValue(entry[2]),
            "fields": {}
        }

        keys = json.loads(self.__decryptAccountValue(entry[3]))
        values = json.loads(self.__decryptAccountValue(entry[4]))

        for k, v in itertools.izip(keys, values):
            account["fields"][k] = v

        return account

    def __decryptAccountValue(self, value):
        decryptedValue = base64.b64decode(value)
        decryptedValue = self.__cipher.decrypt(decryptedValue)
        decryptedValue = self.__removePadding(decryptedValue)
        return decryptedValue

    def __addPadding(self, item):
        return item + (self.__paddingChar * ((16-len(item)) % 16))