import unittest

from unittest.mock import patch, Mock

import requests

from model.config import AccountData, AccountTypes
from services.util import DropboxAccountTester, InvalidAccountCredentialsException


class DropBoxAccountTesterTests(unittest.TestCase):

    def setUp(self):
        testAccountData = AccountData(accountType=AccountTypes.Dropbox, identifier="testID", cryptoKey="sixteen byte key", data={"apiToken": "testApiToken"})
        self.accountTester = DropboxAccountTester(testAccountData)

    @patch("requests.post")
    def test_does_not_raise_exception_if_receives_a_200_OK(self, requests_postMock):
        requests_postMock.return_value = Mock(status_code=200)
        try:
            self.accountTester.validate()
        except InvalidAccountCredentialsException:
            self.fail("DropboxAccountTester raised an exception upon receiving a 200_OK response!")
        self.assertEqual(requests_postMock.call_args[1]["headers"]["Authorization"], "Bearer testApiToken")

    @patch("requests.post")
    def test_raises_an_exception_if_receives_a_non_200_OK_response(self, requests_postMock):
        requests_postMock.return_value = Mock(status_code=400)

        with self.assertRaises(InvalidAccountCredentialsException) as ctx:
            self.accountTester.validate()
