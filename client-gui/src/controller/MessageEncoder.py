import base64

from Crypto.Cipher import AES
from PyQt4 import QtCore


class MessageEncoder(object):

    def __init__(self):
        self.__settings = QtCore.QSettings()
        self.__encryptionKey = unicode(self.__settings.value("commKey").toString()).encode("utf8")
        self.__paddingChar = " "

    def decryptMessage(self, message):
        cipher = AES.new(self.__encryptionKey)
        decryptedMessage = base64.b64decode(message)
        decryptedMessage = cipher.decrypt(decryptedMessage)
        decryptedMessage = self.__unPadMessage(decryptedMessage)
        return decryptedMessage

    def __unPadMessage(self, message):
        return message.rstrip(self.__paddingChar)

    def encryptMessage(self, message):
        cipher = AES.new(self.__encryptionKey)
        paddedMessage = self.__padMessage(message)
        encryptedMessage = cipher.encrypt(paddedMessage)
        return base64.b64encode(encryptedMessage)

    def __padMessage(self, message):
        return message + (self.__paddingChar * ((16-len(message)) % 16))