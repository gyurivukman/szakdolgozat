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
        if("edit" in kwargs and "data" in kwargs):
            self.__setup(True, kwargs["data"])
        else:
            self.__setup(False, None)

    def __setBackgroundColor(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self.setPalette(palette)

    def __setup(self, isEditMode, accData):
        self.layout = QtGui.QVBoxLayout()
        self.__setupCombobox()

        if not isEditMode:
            self.__setupForNewAccount()
        else:
            self.__setupForEditingAnAccount(accData)

        self.layout.addStretch()
        saveButton = QtGui.QPushButton("Save")
        saveButton.clicked.connect(self.__saveAccount)
        self.layout.addWidget(saveButton)
        self.setLayout(self.layout)
    
    def __setupCombobox(self):
        combobox = QtGui.QComboBox(self)
        for account in AccountSchemas.accountSchemas:
            combobox.addItem(account["name"])
        combobox.activated.connect(self.__accountTypeSelected)
        self.layout.addWidget(QtGui.QLabel('Select account type'))
        self.layout.addWidget(combobox)

    def __setupForNewAccount(self):
        self.setFixedSize(300, 100+(len(AccountSchemas.accountSchemas[0]["fields"])+1)*40)
        self.accountPanel = self.panelBuilder.buildFromSchema(AccountSchemas.accountSchemas[0])
        self.layout.addWidget(self.accountPanel['panel'])

    def __setupForEditingAnAccount(self, data):
        schemaIndex = self.__findSchema(data['account_type'])
        self.accountPanel = self.panelBuilder.buildFromSchema(AccountSchemas.accountSchemas[schemaIndex])
        self.__accountTypeSelected(schemaIndex)
        self.__fillPanelWithData(data)

    def __fillPanelWithData(self, data):
        self.accountPanel["set_display_name"](data["display_name"])
        fieldIndex = 0
        for field in self.accountPanel["bindings"]:
            field["setter"](data["fields"][field["name"]])
            fieldIndex = fieldIndex + 1

    def __findSchema(self, accType):
        index = 0
        found = False
        while(index < len(AccountSchemas.accountSchemas) and not found):
            found = AccountSchemas.accountSchemas[index]["name"] == accType
            if not found:
                index = index + 1
        return index

    def __accountTypeSelected(self, accIndex):
        self.setFixedSize(300, 100+(len(AccountSchemas.accountSchemas[accIndex]["fields"])+1)*40)
        self.accountPanel["panel"].setParent(None)
        self.accountPanel = self.panelBuilder.buildFromSchema(AccountSchemas.accountSchemas[accIndex])
        self.layout.insertWidget(2, self.accountPanel["panel"])

    def __saveAccount(self):
        data = {
            "account_type": self.accountPanel['account_type'],
            "display_name": unicode(self.accountPanel["get_display_name"]()).encode("utf8"),
            "fields": {}
        }

        for binding in self.accountPanel['bindings']:
            value = unicode(binding['value']())
            data["fields"][binding['name']] = value
        self.dataEmitter.emit(data)
