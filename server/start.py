import signal
import sys

from control.server import ThreadedServer

if __name__ == "__main__":
    t = ThreadedServer()
    signal.signal(signal.SIGINT, t.stop)
    t.start()