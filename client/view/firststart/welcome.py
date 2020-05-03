from PyQt5.QtWidgets import QVBoxLayout, QLabel

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from view import resources
from view.firststart.abstract import FirstStartWizardMiddleWidget


class WelcomeWidget(FirstStartWizardMiddleWidget):

    def _setup(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 50, 0, 0)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignTop)

        welcomeLabel = QLabel("Welcome to CryptStorePi!")
        welcomeLabel.setAttribute(Qt.WA_TranslucentBackground)
        welcomeLabelFont = QFont('Nimbus Sans L', 42, QFont.Normal)
        welcomeLabel.setFont(welcomeLabelFont)

        welcomeInstructionsLabel = QLabel("This wizard will guide you through the first setup of this application.")
        welcomeInstructionsLabel.setFont(QFont('Nimbus Sans L', 18, QFont.Normal))
        welcomeInstructionsLabel.setAttribute(Qt.WA_TranslucentBackground)
        continueInstructionLabel = QLabel("To start, click 'Next'!")
        continueInstructionLabel.setFont(QFont('Nimbus Sans L', 16, QFont.Normal))
        continueInstructionLabel.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(welcomeLabel, 0, Qt.AlignHCenter | Qt.AlignTop)
        layout.addWidget(welcomeInstructionsLabel, 0, Qt.AlignHCenter)
        layout.addWidget(continueInstructionLabel, 0, Qt.AlignHCenter)
        self.setLayout(layout)

    def canProceed(self):
        return True

    def canGoBack(self):
        return False

    def _getStyle(self):
        self.setObjectName("welcomeWidget")
        return "#welcomeWidget{background-image:url(:encryptionBackground.png);background-repeat:no-repeat;background-position:center;}"
