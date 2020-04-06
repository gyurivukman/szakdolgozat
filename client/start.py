import sys
import logging
import signal
import argparse

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtCore import QCoreApplication, QSettings, Qt
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
parser.add_argument("--loglevel", dest="loglevel", type=str, action="store", default="debug", required=False, choices=["debug", "info", "warning", "error", "off"], help="Log level for the client")


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


if __name__ == '__main__':
    arguments = parser.parse_args()

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
