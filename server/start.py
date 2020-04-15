import logging
import argparse

from sys import stdout

from control.server import Server
import control.cli

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
parser.add_argument("--key", dest="key", type=control.cli.AESKeyArgumentValidator.validate, action="store", required=True, help="16 byte AES encryption key to be used during network communications.")
parser.add_argument("--workspace", dest="workspace", type=control.cli.WorkspaceArgumentValidator.validate, action=control.cli.CreateWorkspaceAction, required=True, help="16 byte AES encryption key to be used during network communications.")
parser.add_argument("--loglevel", dest="loglevel", type=str, action="store", default="debug", required=False, choices=["debug", "info", "warning", "error", "off"], help="Log level for the server")


if __name__ == "__main__":
    control.cli.CONSOLE_ARGUMENTS = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
        level=argumentToLogLevelMap[control.cli.CONSOLE_ARGUMENTS.loglevel],
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=stdout
    )

    rootLogger.info("Starting server")
    googleLogger = logging.getLogger("googleapiclient")
    googleLogger.setLevel(60)  # TODO temporary
    server = Server(control.cli.CONSOLE_ARGUMENTS.port, control.cli.CONSOLE_ARGUMENTS.key)
    try:
        server.start()
    except KeyboardInterrupt:
        rootLogger.info("Received keyboard interrupt, stopping server")
        server.stop()
