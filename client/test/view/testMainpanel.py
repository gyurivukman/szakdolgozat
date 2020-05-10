import unittest
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication, QWidget

from services.hub import ServiceHub
from model.message import MessageTypes
from model.file import FileStatuses


class TestMainPanel(unittest.TestCase):

    @patch.object(ServiceHub, "getInstance")
    def test_syncFiles_sends_retrieve_files_message_with_callback(self, mockGetInstance):
        fakeHub = MagicMock()
        mockGetInstance.return_value = fakeHub

        from view.mainpanel import MainPanel
        app = QApplication([])
        testMainPanelWidget = MainPanel()

        testMainPanelWidget.syncFileList()

        testMainPanelWidget.deleteLater()
        app.deleteLater()
        app.quit()

        self.assertEqual(fakeHub.sendNetworkMessage.call_args[0][0].header.messageType, MessageTypes.SYNC_FILES)
        self.assertIsNotNone(fakeHub.sendNetworkMessage.call_args[0][1])
