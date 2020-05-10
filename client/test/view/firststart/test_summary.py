import unittest
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication, QWidget

from view.firststart.summary import FirstStartSummaryWidget


class TestFirstStartSummaryWidget(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.testSummaryWidget = FirstStartSummaryWidget()

    def tearDown(self):
        self.testSummaryWidget.deleteLater()
        self.app.deleteLater()
        self.app.quit()

    def test_can_always_go_back(self):
        self.assertTrue(self.testSummaryWidget.canGoBack())

    def test_can_never_proceed(self):
        self.assertFalse(self.testSummaryWidget.canProceed())
