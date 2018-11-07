from ConfigParser import ConfigParser
import os


class SettingsWrapper(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SettingsWrapper, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Settings(object):
    __metaclass__ = SettingsWrapper
    __config = None
    __isFirstStart = False
    __CONF_FILE = './settings.conf'

    def __init__(self):
        if not self.__config:
            self.__config = ConfigParser()
        if not os.path.exists(self.__CONF_FILE):
            self.__isFirstStart = True
            self.__createConfigFile()
            self.__addSections()

    def __createConfigFile(self):
        file = open(self.__CONF_FILE, 'w+')
        file.close()

    def __addSections(self):
        self.__config.add_section('NETWORK')
        self.__config.add_section('USER')
        self.__config.add_section('ACCOUNTS')
        print self.__config.has_section('NETWORK')
        with open(self.__CONF_FILE) as f:
            self.__config.write(f)

    def isFirstStart(self):
        return self.__isFirstStart
