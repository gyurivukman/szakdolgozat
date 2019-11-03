from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton


class HelpDialog(QDialog):

    def __init__(self, *args, **kwargs):
        scrollWidget = kwargs.pop('scrollWidget')
        super().__init__(*args, **kwargs)
        self.setObjectName("self")
        self.setStyleSheet(
            """
                QDialog#self{background-color:white;}
                QPushButton#closeHelpButton{
                    background-color:#e36410;
                    color:white;
                    width:150px;
                    border:0px;
                    height:30px;
                    margin-right:5px;
                }
                QPushButton#closeHelpButton:pressed {background-color:#e68a4e;}
                QLabel, QScrollArea{background-color:white;border:0px;}
            """
        )
        self.setFixedSize(480, 720)
        self._setup(scrollWidget)
    
    def _setup(self, scrollWidget):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        scroll = QScrollArea()
        scroll.setWidget(scrollWidget)
        scroll.setWidgetResizable(False)
        scroll.setFixedHeight(680)
        
        controlLayout = QHBoxLayout()
        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.hide)
        closeButton.setObjectName("closeHelpButton")
        controlLayout.setAlignment(Qt.AlignRight)
        controlLayout.addWidget(closeButton)

        layout.addWidget(scroll)
        layout.addLayout(controlLayout)
        layout.addStretch(1)
        self.setLayout(layout)
