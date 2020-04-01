import sys
import logging
import signal

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtCore import QCoreApplication, QSettings, Qt
from PyQt5.QtGui import QIcon

from view.mainwindow import MainWindow
from view import resources


app = None
mainWindow = None
trayIcon = None
signal.signal(signal.SIGINT, signal.SIG_DFL)


logger = logging.getLogger()


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
    logger.info("Exiting, please wait...")
    trayIcon.hide()
    mainWindow.hide()
    mainWindow.stop()
    app.quit()


def createTrayMenu():
    menu = QMenu()

    openAction = menu.addAction("Open")
    openAction.triggered.connect(showMainWindow)

    # settingsAction = menu.addAction("Settings")
    # settingsAction.triggered.connect(onSettingsClicked)

    exitAction = menu.addAction("Exit")
    exitAction.triggered.connect(onExit)

    return menu


# def onSettingsClicked():
#     settings = QSettings()
#     isFirstStart = not settings.contains('IsFirstStart') or settings.contains('IsFirstStart') and settings.value('IsFirstStart').toBool()

#     if isFirstStart:
#         mainWindow.show()
#     else:
#         pass


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(name)s    [%(levelname)s]    %(message)s',
        level=logging.DEBUG,
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
