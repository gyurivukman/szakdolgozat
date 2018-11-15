from PyQt4 import QtGui, QtCore
from src.controller.AuthenticationController import AuthenticationController

class LoginForm(QtGui.QWidget):
    loggedIn = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QtGui.QWidget, self).__init__(*args, **kwargs)
        self.__setupGui()
        
        self.auth = AuthenticationController()
    
    def __setupGui(self):
        self.setFixedSize(300, 230)
        self.__setLayout()
        self.__setBackgroundColor()
        self.__setStyle()

    def __setLayout(self):
        layout = QtGui.QFormLayout(self)

        self.__setupUsernameField(layout)
        self.__setupPasswordField(layout)
        self.__setupErrorLabel(layout)
        self.__setupLoginButton(layout)

        self.setLayout(layout)

    def __setupUsernameField(self, layout):
        layout.addRow(QtGui.QLabel('Username:'))
        self.usernameField = QtGui.QLineEdit()
        self.usernameField.setObjectName('usernameField')
        layout.addRow(self.usernameField)

    def __setupPasswordField(self, layout):
        layout.addRow(QtGui.QLabel('Password:'))
        self.passwordField = QtGui.QLineEdit()
        self.passwordField.setObjectName('passwordField')
        self.passwordField.setEchoMode(QtGui.QLineEdit.Password)
        layout.addRow(self.passwordField)

    def __setupLoginButton(self, layout):
        loginButton = QtGui.QPushButton('Login')
        loginButton.clicked.connect(self.__attemptLogin)
        layout.addRow(loginButton)
    
    def __setupErrorLabel(self, layout):
        self.errorLabel = QtGui.QLabel('')
        self.errorLabel.setObjectName('errorLabel')
        layout.addRow(self.errorLabel)

    def __setBackgroundColor(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self.setPalette(palette)

    def __attemptLogin(self):
        uname = self.usernameField.text()
        pwd = self.passwordField.text()
        if(not self.auth.login(uname, pwd)):
            self.errorLabel.setText('Wrong credentials!')
        else:
            self.errorLabel.setText('')
            self.loggedIn.emit()

    def __setStyle(self):
        self.setAutoFillBackground(True)

        self.setStyleSheet(
            """
                #usernameField { 
                    margin-bottom:10px;
                }
                #errorLabel {
                    margin-top:10px;
                    margin-left:auto;
                    margin-right:auto;
                }
                .QPushButton {
                    width:75%;
                    margin-left:auto;
                    margin-right:auto;
                    height:30px;
                    background-color:#7ae6ff;
                }
                .QLabel {
                    margin-left:auto;
                    margin-right:auto;
                }
                .QLineEdit {
                    border:2px solid black;
                    border-radius:3px;
                    width: 75%;
                    margin-left:auto;
                    margin-right:auto;
                    height:30px;
                    font-size:18px;
                }
                .QLineEdit:focus {
                    border-color:#09c5ef;
                }
            """
        )
