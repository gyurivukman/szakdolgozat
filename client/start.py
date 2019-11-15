import sys
import logging

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtGui import QIcon
from view.MainWindow import MainWindow

app = None
mainWindow = None


def setupOrganization():
    QCoreApplication.setOrganizationName('elte')
    QCoreApplication.setApplicationName('cryptstorepi')


def createTrayIcon():
    trayIcon = QSystemTrayIcon(QIcon('view/assets/logo.png'), app)
    trayIcon.setContextMenu(createTrayMenu())
    return trayIcon


def createTrayMenu():
    menu = QMenu()

    openAction = menu.addAction("Open")
    openAction.triggered.connect(onOpenClicked)

    settingsAction = menu.addAction("Settings")
    settingsAction.triggered.connect(onSettingsClicked)

    exitAction = menu.addAction("Exit")
    exitAction.triggered.connect(app.quit)

    return menu


def onOpenClicked():
    if mainWindow.isHidden():
        mainWindow.show()


def onSettingsClicked():
    settings = QSettings()
    isFirstStart = not settings.contains('IsFirstStart') or settings.contains('IsFirstStart') and settings.value('IsFirstStart').toBool()

    if isFirstStart:
        mainWindow.show()
    else:
        pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    setupOrganization()
    trayIcon = createTrayIcon()
    trayIcon.show()
    mainWindow = MainWindow()
    mainWindow.initGUI()
    sys.exit(app.exec_())
