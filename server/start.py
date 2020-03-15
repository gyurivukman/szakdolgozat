import logging

from sys import stdout

from control.server import Server

logger = logging.getLogger()

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=stdout
)

if __name__ == "__main__":
    logger.info("Starting server")
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping server")
        server.stop()
