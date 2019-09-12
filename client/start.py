import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from view.FramedViews import MainWindow

def setupOrganization():
    QCoreApplication.setOrganizationName('elte')
    QCoreApplication.setApplicationName('cryptstorepi')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    setupOrganization()
    mainWindow = MainWindow()
    mainWindow.initGUI()
    sys.exit(app.exec_())
