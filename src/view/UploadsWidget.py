from PyQt4 import QtGui


class UploadsWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(UploadsWidget, self).__init__(*args, **kwargs)

        listBox = QtGui.QVBoxLayout(self)
        self.setLayout(listBox)

        scroll = QtGui.QScrollArea(self)
        listBox.addWidget(scroll)
        scroll.setWidgetResizable(True)
        scrollContent = QtGui.QWidget(scroll)

        scrollLayout = QtGui.QVBoxLayout(scrollContent)
        scrollContent.setLayout(scrollLayout)
        for item in range(100):
            scrollLayout.addWidget(QtGui.QLabel(str(item)))
        scroll.setWidget(scrollContent)
