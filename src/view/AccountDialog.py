from PyQt4 import QtGui, QtCore
import src.model.AccountSchemas as AccountSchemas
from src.controller.AccountPanelBuilder import AccountPanelBuilder

class AccountDialog(QtGui.QDialog):
    dataEmitter = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super(AccountDialog, self).__init__()
        self.setWindowTitle("Account")
        self.panelBuilder = AccountPanelBuilder()
        self.__setBackgroundColor()
        self.__setupForNewAccount()

    def __setBackgroundColor(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self.setPalette(palette)

    def __setupForNewAccount(self):
        self.setFixedSize(300, 200)
        self.layout = QtGui.QVBoxLayout()
        combobox = QtGui.QComboBox(self)
        for account in AccountSchemas.accountSchemas:
            combobox.addItem(account["name"])
        combobox.activated.connect(self.__accountTypeSelected)

        self.layout.addWidget(QtGui.QLabel('Select account type'))
        self.layout.addWidget(combobox)

        self.accountPanel = self.panelBuilder.buildFromSchema(AccountSchemas.accountSchemas[0])
        self.layout.addWidget(self.accountPanel['panel'])

        saveButton = QtGui.QPushButton("Save")
        saveButton.clicked.connect(self.__saveAccount)
        self.layout.addWidget(saveButton)
        self.setLayout(self.layout)
        
    def __accountTypeSelected(self, accIndex):
        self.accountPanel["panel"].setParent(None)
        self.accountPanel = self.panelBuilder.buildFromSchema(AccountSchemas.accountSchemas[accIndex])
        self.layout.insertWidget(2, self.accountPanel["panel"])

    def __saveAccount(self):
        data = {}
        for binding in self.accountPanel['bindings']:
            value = unicode(binding['value']())
            data[binding['name']] = value
        self.dataEmitter.emit(data)
