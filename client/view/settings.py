from PyQt5.QtWidgets import QWidget, QDialog, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("CryptStorePi Settings")
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedSize(1280, 720)

        layout = self.__createLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def __createLayout(self):
        layout = QHBoxLayout()
        settingsMenu = SettingsMenuPanel()
        networkSettings = NetworkSettings()

        layout.addWidget(settingsMenu)
        layout.addWidget(networkSettings)
        return layout


class SettingsMenuPanel(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedSize(180, 720)
        self.setObjectName("self")

        self.setStyleSheet("#self{border:1px solid green;}")

        layout = self.__createLayout()
        self.setLayout(layout)

    def __createLayout(self):
        layout = QVBoxLayout()
        label = QLabel("MENU PLACEHOLDER")

        layout.addWidget(label)
        layout.addStretch(1)

        return layout


class NetworkSettings(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedSize(1100, 720)
        self.setObjectName("self")

        self.setStyleSheet("#self{border:1px solid purple;}")

        layout = self.__createLayout()
        self.setLayout(layout)

    def __createLayout(self):
        layout = QVBoxLayout()
        label = QLabel("NETWORK PLACEHOLDER")

        layout.addWidget(label)
        layout.addStretch(1)

        return layout
