import base64

from Crypto.Cipher import AES


class MessageEncoder(object):

    def __init__(self, encryptionKey):
        self.encryptionKey = encryptionKey
        self.paddingChar = " "

    def decryptMessage(self, message):
        cipher = AES.new(self.encryptionKey)
        decryptedMessage = base64.b64decode(message)
        decryptedMessage = cipher.decrypt(message)
        decryptedMessage = self.__unPadMessage(message)
        return decryptedMessage

    def __unPadMessage(self, message):
        return message.rstrip(self.paddingChar)

    def encryptMessage(self, message):
        cipher = AES.new(self.encryptionKey)
        paddedMessage = self.__padMessage(message)
        encryptedMessage = cipher.encrypt(paddedMessage)
        return base64.b64encode(encryptedMessage)

    def __padMessage(self, message):
        return message + (self.paddingChar * ((16-len(message)) % 16))