import configparser, logging
from os import stat as stat


class ServerConfiguration():

    def __init__(self):
        self.__logger = logging.getLogger("Config")
        self.__configFile = "config.ini"
        self.__parser = configparser.ConfigParser()
    
    def isConfigured(self):
        return self.__doesConfigFileExists() and self.__parser

    def parseConfiguration(self):
        self.__parser.read(self.__configFile)
    
    def  __doesConfigFileExists(self):
        try:
            stat(self.__configFile)
            return True
        except FileNotFoundError:
            return False
