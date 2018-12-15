import sys
import os
import datetime
from functools import partial

from Crypto.Cipher import AES


class FileEncoder(object):
    def __init__(self):
        self.__paddingChar = " "
        self.__encoder = AES.new(self.__findEncryptionKeyInSysArgs())

    def encryptFile(self, localPath):
        output = '{}.enc'.format(localPath)
        with open(localPath, 'rb') as inputfile:
            with open(output, 'wb') as output:
                for chunk in iter(partial(inputfile.read, 256), ''):
                    if len(chunk) < 256:
                        chunk = self.__addPadding(chunk)
                    encrypted = self.__encoder.encrypt(chunk)
                    output.write(encrypted)
        newModificationDate = datetime.datetime.fromtimestamp(int(os.stat(localPath).st_mtime)).strftime("%Y%m%d%H%M.%S")
        os.system("touch -mt {} {}".format(newModificationDate, output))
        os.remove(localPath)

    def decryptFile(self, localPath):
        decryptedPath = localPath.split('.enc')[0]
        with open(localPath, 'rb') as inputfile:
            with open(decryptedPath, 'wb') as output:
                for chunk in iter(partial(inputfile.read, 256), ''):
                    decrypted = self.__removePadding(self.__encoder.decrypt(chunk))
                    output.write(decrypted)
        os.remove(localPath)
        os.system('chmod -R o+rw {}'.format(decryptedPath))
        
    def __findEncryptionKeyInSysArgs(self):
        found = False
        args = sys.argv
        index = 0
        while not found:
            found = args[index] == '--encryptionkey'
            if not found:
                index = index + 1
        return args[index+1]
    
    def __addPadding(self, chunk):
        return chunk + (self.__paddingChar * ((16-len(chunk)) % 16))

    def __removePadding(self, chunk):
        return chunk.rstrip(self.__paddingChar)
