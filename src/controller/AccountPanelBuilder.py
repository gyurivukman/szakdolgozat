from PyQt4 import QtGui

class AccountPanelBuilder(object):

    def buildFromSchema(self, schema):
        self.bindingSchema = []
        container = QtGui.QWidget()
        containerLayout = QtGui.QVBoxLayout(container)
        containerLayout.addLayout(self.__buildDisplayNamePanel())
        for field in schema['fields']:
            containerLayout.addLayout(self.__buildPartial(field))
        container.setLayout(containerLayout)
        return {
            "account_type": schema['name'],
            "get_display_name": self.displayNameField.text,
            "set_display_name": self.displayNameField.setText,
            "panel": container,
            "bindings": self.bindingSchema
        }

    def __buildDisplayNamePanel(self):
        layout = QtGui.QHBoxLayout()
        self.displayNameField = QtGui.QLineEdit()
        layout.addWidget(QtGui.QLabel("Name your account:"))
        layout.addWidget(self.displayNameField)

        return layout

    def __buildPartial(self, fieldSchema):
        layout = QtGui.QHBoxLayout()
        layout.addWidget(QtGui.QLabel(fieldSchema['display_name']))
        if(fieldSchema['type'] == "text"):
            field = QtGui.QLineEdit()
            layout.addWidget(field)
            self.bindingSchema.append(
                {
                    "name": fieldSchema['model_name'],
                    "value": field.text,
                    "setter": field.setText
                }
            )

        elif(fieldSchema['type'] == "password"):
            field = QtGui.QLineEdit()
            field.setEchoMode(QtGui.QLineEdit.Password)
            layout.addWidget(field)
            self.bindingSchema.append(
                {
                    "name": fieldSchema['model_name'],
                    "value": field.text,
                    "setter": field.setText
                }
            )
        
        return layout
