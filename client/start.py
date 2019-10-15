import sys

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from view.FramedViews import MainWindow

app = None
mainWindow = None

def setupOrganization():
    QCoreApplication.setOrganizationName('elte')
    QCoreApplication.setApplicationName('cryptstorepi')
def createTrayIcon():
    trayIcon = QSystemTrayIcon(QIcon('view/assets/logo.png'), app)
    trayIcon.activated.connect(iconActivated)
    trayIcon.setContextMenu(createTrayMenu())
    return trayIcon

def createTrayMenu():
    menu = QMenu()

    openAction = menu.addAction("Open")
    openAction.triggered.connect(onOpenClicked)

    exitAction = menu.addAction("Exit")
    exitAction.triggered.connect(app.exit)

    return menu

def onOpenClicked():
    if mainWindow.isHidden():
        mainWindow.show()

def iconActivated(reason):
    if reason == QSystemTrayIcon.DoubleClick:
        mainWindow.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    setupOrganization()
    trayIcon = createTrayIcon()
    trayIcon.show()
    mainWindow = MainWindow()
    mainWindow.initGUI()
    sys.exit(app.exec_())
