from PyQt4 import QtCore, QtGui

from StatusWidget import StatusWidget


class ItemSheet(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(ItemSheet, self).__init__(args[0], args[1], **kwargs)
        self.__setup(args[2], args[3])
    
    def __setup(self, itemPath, status):
        self.itemState = status
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.setFixedHeight(45)
        self.__setupItemPathLabel(itemPath)
        self.__setupStatusWidget(status)

        self.setStyleSheet(
            """
                QWidget {
                    border:0px solid transparent;
                    border-bottom:2px solid #F2F2F2;
                }
            """
        )

        self.setLayout(self.layout)

    def __setupItemPathLabel(self, itemPath):
        if(len(itemPath)>39):
            self.itemPath = QtGui.QLabel(itemPath[:37]+"...", parent=self)
            self.setToolTip(itemPath)
        else:
            self.itemPath = QtGui.QLabel(itemPath, parent=self)
        self.layout.addWidget(self.itemPath)
    
    def __setupStatusWidget(self, status):
        self.layout.addWidget(StatusWidget(self))
        #self.layout.addWidget(QtGui.QLabel('TESZT'))
