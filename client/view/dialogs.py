from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class ConnectionErrorDialog(QDialog):

    def __init__(self, *args, **kwargs):
        errorMessage = kwargs.pop("messageText")
        super().__init__(*args, **kwargs)
        self._userInputResult = None
        self._setupPanel(errorMessage)

    def _setupPanel(self, errorMessage):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(errorMessage))

        retryButton = QPushButton("Retry")
        retryButton.clicked.connect(self._onRetryClicked)
        exitButton = QPushButton("Exit")
        exitButton.clicked.connect(self._onExitClicked)

        layout.addWidget(retryButton)
        layout.addWidget(exitButton)
        self.setLayout(layout)

    def _onRetryClicked(self, _):
        self._userInputResult = True

    def _onExitClicked(self, _):
        self._userInputResult = False
