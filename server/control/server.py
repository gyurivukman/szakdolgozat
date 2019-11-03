from control.configuration import ServerConfiguration
from sys import exit as exit
import logging
import time


class ThreadedServer():

    def __init__(self):
        self.__config = ServerConfiguration()
        self.__logger = logging.getLogger("Server")
    
    def start(self):
        try:
            self.__config.parseConfiguration()
            while True:
                print("derpa")
                time.sleep(3)
        except FileNotFoundError as e:
            self.__logger.error("File 'config.ini' not found.")

    def stop(self, sig, frame):
        self.__logger('Received kill signal, shutting down...')
        exit(0)