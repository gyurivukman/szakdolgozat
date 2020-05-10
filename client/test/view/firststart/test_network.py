import unittest
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication, QWidget

from view.firststart.network import SetupNetworkWidget


class TestSetupNetworkWidget(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.testNetworkWidget = SetupNetworkWidget()

    def tearDown(self):
        self.testNetworkWidget.deleteLater()
        self.app.deleteLater()
        self.app.quit()

    def test_can_always_go_back(self):
        self.assertTrue(self.testNetworkWidget.canGoBack())
