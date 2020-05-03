import sys
import logging
import signal
import argparse

from os import unlink
from os.path import expanduser

import paramiko

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from view.mainwindow import MainWindow
from view import resources


app = None
mainWindow = None
trayIcon = None
signal.signal(signal.SIGINT, signal.SIG_DFL)


rootLogger = logging.getLogger()

argumentToLogLevelMap = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "off": 60
}

parser = argparse.ArgumentParser(prog="CryptStorePi Client")
parser.add_argument("--logLevel", dest="loglevel", type=str, action="store", default="debug", required=False, choices=["debug", "info", "warning", "error", "off"], help="Log level for the client")
parser.add_argument("--purgeSettings", dest="purge", action="store_true", required=False, help="Remove all the settings, resetting the client. USE THIS WITH CAUTION!")
parser.add_argument("--thirdPartyLogging", dest="thirdPartyLogging" ,action="store_true", required=False, help="Turn third party component logging on")


def setupOrganization():
    QCoreApplication.setOrganizationName('elte')
    QCoreApplication.setApplicationName('cryptstorepi')


def createTrayIcon():
    trayIcon = QSystemTrayIcon(QIcon(':logo.png'), app)
    trayIcon.setContextMenu(createTrayMenu())
    trayIcon.activated.connect(trayIconActivated)

    return trayIcon


def trayIconActivated(reason):
    if reason == QSystemTrayIcon.DoubleClick:
        showMainWindow()


def showMainWindow():
    if mainWindow.isHidden():
        mainWindow.show()
    mainWindow.activateWindow()


def onExit():
    rootLogger.info("Exiting, please wait...")
    trayIcon.hide()
    mainWindow.hide()
    mainWindow.stop()
    app.quit()


def createTrayMenu():
    menu = QMenu()

    openAction = menu.addAction("Open")
    openAction.triggered.connect(showMainWindow)

    exitAction = menu.addAction("Exit")
    exitAction.triggered.connect(onExit)

    return menu


def confirmPurge():
    userChoice = input("Are you sure you want to remove all the settings and reset CryptStorePi? Y/N: ")
    if userChoice == "Y":
        try:
            unlink(f"{expanduser('~')}/.config/elte/cryptstorepi.conf")
        except FileNotFoundError as _:
            pass
    elif userChoice != "N":
        print("Unknown choice! Please use either 'Y' or 'N' as your answer.")
        sys.exit(0)


if __name__ == '__main__':
    arguments = parser.parse_args()
    if arguments.purge:
        confirmPurge()

    if not arguments.thirdPartyLogging:
        logging.getLogger("paramiko").setLevel(60)
        logging.getLogger("watchdog").setLevel(60)

    logging.basicConfig(
        format='%(asctime)s %(name)s    [%(levelname)s]    %(message)s',
        level=argumentToLogLevelMap[arguments.loglevel],
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    app = QApplication(sys.argv)
    setupOrganization()
    trayIcon = createTrayIcon()
    trayIcon.show()
    mainWindow = MainWindow()
    mainWindow.initGUI()
    sys.exit(app.exec_())
