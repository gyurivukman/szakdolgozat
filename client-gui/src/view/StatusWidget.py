from PyQt4 import QtGui


class StatusWidget(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(StatusWidget, self).__init__(args[0], **kwargs)
        self.__status = args[1]
        self.__setup()

    def __setup(self):
        self.__statusLabel = QtGui.QLabel("KUKKEN") #str(self.__status)
        self.__layout = QtGui.QHBoxLayout()
        self.__layout.addWidget(self.__statusLabel)
        self.setFixedWidth(100)
        self.setFixedHeight(45)

    def updateStatus(self, status):
        self.__statusLabel = QtGui.QLabel(str(self.__status))
        self.repaint()
        # self.setStyleSheet(
        #     """
        #         QWidget {
        #             border:0px solid transparent;
        #             border-bottom:2px solid #F2F2F2;
        #         }
        #     """
        # )

    # def paintEvent(self, e):
    #     option = QtGui.QStyleOption()
    #     option.initFrom(self)
    #     qp = QtGui.QPainter()
    #     qp.begin(self)
    #     self.style().drawPrimitive(
    #         QtGui.QStyle.PE_Widget, option, qp, self)
    #     self.drawWidget(qp)
    #     qp.end()
    
    # def drawWidget(self, qp):
    #     qp.setPen(QtGui.QColor(0, 0, 0))
    #     qp.setBrush(QtGui.QColor(0, 255, 0))
    #     qp.drawRect(0, 15, 15, 15)
    #     qp.setBrush(QtGui.QColor(0, 255, 0))
    #     qp.drawRect(25, 15, 15, 15)
    #     qp.setBrush(QtGui.QColor(255, 255, 0))
    #     qp.drawRect(50, 15, 15, 15)
    #     qp.setBrush(QtGui.QColor(255, 255, 255))
    #     qp.drawRect(75, 15, 15, 15)
