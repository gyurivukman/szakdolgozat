from PyQt4 import QtGui

class AccountPanelBuilder(object):

    def buildFromSchema(self, schema):
        self.bindingSchema = []
        container = QtGui.QWidget()
        containerLayout = QtGui.QVBoxLayout(container)

        for field in schema['fields']:
            containerLayout.addLayout(self.__buildPartial(field))
        containerLayout.addStretch()
        container.setLayout(containerLayout)
        return {
            "panel": container,
            "bindings": self.bindingSchema
        }

    def __buildPartial(self, fieldSchema):
        layout = QtGui.QHBoxLayout()
        layout.addWidget(QtGui.QLabel(fieldSchema['name']))
        if(fieldSchema['type'] == "text"):
            field = QtGui.QLineEdit()
            layout.addWidget(field)
            self.bindingSchema.append(
                {
                    "name": fieldSchema['name'],
                    "value": field.text
                }
            )

        elif(fieldSchema['type'] == "password"):
            field = QtGui.QLineEdit()
            field.setEchoMode(QtGui.QLineEdit.Password)
            layout.addWidget(field)
            self.bindingSchema.append(
                {
                    "name":fieldSchema['name'],
                    "value":field.text
                }
            )
        
        return layout
