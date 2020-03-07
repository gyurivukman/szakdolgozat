import logging

from sys import stdout

from server import Server


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=stdout
)

if __name__ == "__main__":
    rootlogger = logging.getLogger('[rootlogger]')
    rootlogger.setLevel(logging.DEBUG)
    rootlogger.addHandler(logging.StreamHandler(stdout))
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        rootlogger.debug("Received keyboard interrupt, shutting down")
        server.stop()
