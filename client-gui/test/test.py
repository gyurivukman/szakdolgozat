import unittest
import json
from mock import patch
from PyQt4 import QtCore
from src.controller.MessageEncoder import MessageEncoder


class TestMessageEncoder(unittest.TestCase):

    @patch.object(QtCore.QSettings, "value")
    def test_empty(self, settings):
        settings.return_value = StringHelper("G+KbPeShVmYq3t6w")
        encoder = MessageEncoder()
        self.assertSymetry(encoder, "")

    @patch.object(QtCore.QSettings, "value")
    def test_simple_text(self, settings):
        settings.return_value = StringHelper("G+KbPeShVmYq3t6w")
        encoder = MessageEncoder()
        self.assertSymetry(encoder, "FOO")

    @patch.object(QtCore.QSettings, "value")
    def test_simple_text_longer_key(self, settings):
        settings.return_value = StringHelper("1D1D4AEA03AF7C4FB74754BF12FEC62C")
        encoder = MessageEncoder()
        self.assertSymetry(encoder, "FOO")

    @patch.object(QtCore.QSettings, "value")
    def test_dict(self, settings):
        settings.return_value = StringHelper("G+KbPeShVmYq3t6w")
        encoder = MessageEncoder()
        self.assertSymetry(encoder, {"simplekey": "value"})

    @patch.object(QtCore.QSettings, "value")
    def test_longmessage(self, settings):
        settings.return_value = StringHelper("G+KbPeShVmYq3t6w")
        encoder = MessageEncoder()
        self.assertSymetry(encoder, "long"*100)

    @patch.object(QtCore.QSettings, "value")
    def test_specialchars(self, settings):
        settings.return_value = StringHelper("G+KbPeShVmYq3t6w")
        encoder = MessageEncoder()
        self.assertSymetry(encoder, u'\u5E73\u621015  ')

    @patch.object(QtCore.QSettings, "value")
    def test_separator(self, settings):
        settings.return_value = StringHelper("G+KbPeShVmYq3t6w")
        encoder = MessageEncoder()
        self.assertSymetry(encoder, ';')

    def assertSymetry(self, encoder, original):
        encoded = encoder.encryptMessage(original)
        decoded = encoder.decryptMessage(encoded)
        text = json.dumps(original)
        self.assertEquals(text, decoded)
        self.assertTrue(text not in encoded[:-1])
        self.assertEquals(encoded[-1], ";")


class StringHelper:

    def __init__(self, text):
        self.text = text

    def toString(self):
        return self.text
