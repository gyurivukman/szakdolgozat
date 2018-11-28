import argparse
import signal

from src.controller.CryptStorePiServer import CryptStorePiServer


def checkArgs(args):
    errors = []
    if args.port < 12000 or args.port > 15000:
        errors.append("Invalid port! Port must be from interval [12000, 15000]")
    if len(args.encryptionkey) != 32:
        errors.append("Insufficient encryption key length! Key must be a 256 bit key")
    return errors

# G+KbPeShVmYq3t6w


def main():
    # parser = argparse.ArgumentParser(description="CryptStorePi server application v0.1")
    # parser.add_argument("--port", type=int, help="Communication port ranging from 12000 to 15000", required=True)
    # parser.add_argument("--encryptionkey", type=str, help="Symmetric encryption key to be used for communicating with the client. You will have to set the same key clientside. Key must be a 256 bit key", required=True)
    # args = parser.parse_args()

    # errors = checkArgs(args)
    errors = None
    if errors:
        print "Errors: "
        for error in errors:
            print error
    else:
        debugPort = 12500
        debugKey = "G+KbPeShVmYq3t6w"
        server = CryptStorePiServer(debugPort, debugKey)
        server.start()

if __name__ == '__main__':
    main()
