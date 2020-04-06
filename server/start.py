import logging
import argparse

from sys import stdout

from control.server import Server

rootLogger = logging.getLogger()

argumentToLogLevelMap = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "off": 60
}

parser = argparse.ArgumentParser(prog="CryptStorePi Server")
parser.add_argument("--port", dest="port", type=int, action="store", required=True, help="Port the server should listen on.")
parser.add_argument("--key", dest="key", type=str, action="store", required=True, help="16 byte AES encryption key to be used during network communications.")
parser.add_argument("--loglevel", dest="loglevel", type=str, action="store", default="debug", required=False, choices=["debug", "info", "warning", "error", "off"], help="Log level for the server")

if __name__ == "__main__":
    arguments = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
        level=argumentToLogLevelMap[arguments.loglevel],
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=stdout
    )

    rootLogger.info("Starting server")
    server = Server(arguments.port, arguments.key)
    try:
        server.start()
    except KeyboardInterrupt:
        rootLogger.info("Received keyboard interrupt, stopping server")
        server.stop()
