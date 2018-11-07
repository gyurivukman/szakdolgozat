from PyQt4 import QtGui, QtCore


class AboutDialog(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(QtGui.QWidget, self).__init__(*args, **kwargs)
        self.__setup()

    def __setup(self):
        self.setWindowTitle('About')
        self.setFixedSize(300, 200)
        self.setWindowIcon(QtGui.QIcon("./resources/logo.png"))
        self.__setBackgroundColor()
        self.__setLayout()

    def __setBackgroundColor(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(palette)

    def __setLayout(self):
        mainLayout = QtGui.QFormLayout(self)

        logoContainer = QtGui.QLabel(self)
        logoContainer.setAlignment(QtCore.Qt.AlignHCenter)
        logo = QtGui.QPixmap("./resources/logo.png")
        logoContainer.setPixmap(logo)
        mainLayout.addRow(logoContainer)

        label = QtGui.QLabel('CryptStorePi', self)
        label.setFont(QtGui.QFont("Arial", 18))
        label.setAlignment(QtCore.Qt.AlignHCenter)
        mainLayout.addRow(label)

        label = QtGui.QLabel('v0.0.1', self)
        label.setFont(QtGui.QFont("Arial", 12))
        label.setAlignment(QtCore.Qt.AlignHCenter)
        mainLayout.addRow(label)
        
        inlineLabelWidget = QtGui.QWidget(self)
        subLayout = QtGui.QHBoxLayout(inlineLabelWidget)

        label = QtGui.QLabel('ELTE', self)
        label.setFont(QtGui.QFont("Sans", 16))
        label.setAlignment(QtCore.Qt.AlignLeft)
        subLayout.addWidget(label)

        label = QtGui.QLabel('2018', self)
        label.setFont(QtGui.QFont("Sans", 16))
        label.setAlignment(QtCore.Qt.AlignRight)
        subLayout.addWidget(label)

        subLayout.insertSpacing(0, 50)
        subLayout.insertSpacing(-1, 50)
        inlineLabelWidget.setLayout(subLayout)
        mainLayout.addRow(inlineLabelWidget)

        self.setLayout(mainLayout)

    def closeEvent(self, event):
        event.ignore()
        self.hide()