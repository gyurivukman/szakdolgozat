import unittest
from unittest.mock import patch, MagicMock

from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QObject, pyqtSignal

from services.hub import ServiceHub
from view.firststart.accounts import SetupAccountsWrapperWidget, SetupAccountsWidget
from model.message import MessageTypes
from model.config import AccountData, AccountTypes


class FakeServiceHub(QObject, MagicMock):
    networkStatusChannel = pyqtSignal(object)

    startNetworkService = MagicMock()
    connectToServer = MagicMock()
    sendNetworkMessage = MagicMock()


class FakeAccountsWidget(QWidget):
    accountListValidityChanged = pyqtSignal(bool)

    def setAccounts(self, accounts):
        self.accounts = accounts
        if len(accounts) > 0:
            self.accountListValidityChanged.emit(True)

    def getAccounts(self):
        return self.accounts

    def removeAllAccounts(self):
        self.accounts = []


class TestSetupAccountsWrapperWidget(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.fakeAccountsWidget = FakeAccountsWidget()

    def tearDown(self):
        self.app.deleteLater()
        self.app.quit()

    @patch("view.firststart.accounts.SetupAccountsWidget")
    @patch.object(ServiceHub, "getInstance")
    def test_initData_starts_network_service_and_retrieves_accountList(self, mockGetInstance, fakeAccountsWidget):
        fakeAccountsWidget.return_value = self.fakeAccountsWidget
        fakeHub = MagicMock()
        mockGetInstance.return_value = fakeHub

        component = SetupAccountsWrapperWidget()
        component.initData()

        self.assertTrue(fakeHub.startNetworkService.called)
        self.assertEqual(fakeHub.startNetworkService.call_count, 1)

        self.assertTrue(fakeHub.connectToServer.called)
        self.assertEqual(fakeHub.connectToServer.call_count, 1)

        self.assertTrue(fakeHub.sendNetworkMessage.called)
        self.assertEqual(fakeHub.sendNetworkMessage.call_count, 1)

        self.assertTrue(fakeHub.networkStatusChannel.connect.called)
        self.assertEqual(fakeHub.networkStatusChannel.connect.call_count, 1)

        networkMessageToBeSent = fakeHub.sendNetworkMessage.call_args[0][0]
        callBackFunction = fakeHub.sendNetworkMessage.call_args[0][1]

        self.assertEqual(networkMessageToBeSent.header.messageType, MessageTypes.GET_ACCOUNT_LIST)
        self.assertIsNotNone(networkMessageToBeSent.header.uuid)
        self.assertIsNotNone(callBackFunction)

        component.deleteLater()

    @patch("view.firststart.accounts.SetupAccountsWidget")
    @patch.object(ServiceHub, "getInstance")
    def test_cannot_proceed_on_empty_account_list(self, mockGetInstance, fakeAccountsWidget):
        fakeAccountsWidget.return_value = self.fakeAccountsWidget
        fakeHub = MagicMock()
        mockGetInstance.return_value = fakeHub

        # testSetupAccountsWidget.return_value = SetupAccountsWidget()

        component = SetupAccountsWrapperWidget()
        component.initData()

        fakeAccountResponse = {"accounts": []}
        callBackFunction = fakeHub.sendNetworkMessage.call_args[0][1]

        callBackFunction(fakeAccountResponse)

        self.assertFalse(component.canProceed())
        self.assertTrue(component.isInited())

    @patch("view.firststart.accounts.SetupAccountsWidget")
    @patch.object(ServiceHub, "getInstance")
    def test_can_proceed_if_server_returns_non_empty_account_list(self, mockGetInstance, fakeAccountsWidget):

        fakeAccountsWidget.return_value = self.fakeAccountsWidget
        fakeHub = MagicMock()
        mockGetInstance.return_value = fakeHub

        component = SetupAccountsWrapperWidget()
        component.initData()

        fakeAccountData = {"accountType": AccountTypes.Dropbox, "identifier": "fakeAccount", "cryptoKey":"sixteen byte key", "data": {"apiToken":"fakeAPIToken"}, "id":1}
        fakeAccountResponse = {"accounts": [fakeAccountData]}
        callBackFunction = fakeHub.sendNetworkMessage.call_args[0][1]

        callBackFunction(fakeAccountResponse)

        self.assertTrue(component.canProceed())

    def test_can_go_back_always_true(self):
        component = SetupAccountsWrapperWidget()
        self.assertTrue(component.canGoBack())

    @patch("view.firststart.accounts.SetupAccountsWidget")
    @patch.object(ServiceHub, "getInstance")
    def test_callBack_sets_retrieved_account_list_into_underlying_accountListComponent(self, mockGetInstance, fakeAccountsWidget):
        testAccountData = AccountData(AccountTypes.Dropbox, "fakeAccount", "sixteen byte key", {"apiToken": "fakeAPIToken"}, 1)
        self.fakeAccountsWidget.accounts = [testAccountData]
        fakeAccountsWidget.return_value = self.fakeAccountsWidget
        fakeHub = MagicMock()
        mockGetInstance.return_value = fakeHub

        component = SetupAccountsWrapperWidget()
        accountData = component.getFormData()

        self.assertEqual(len(accountData), 1)

        self.assertEqual(testAccountData.accountType, accountData[0].accountType)
        self.assertEqual(testAccountData.identifier, accountData[0].identifier)
        self.assertEqual(testAccountData.cryptoKey, accountData[0].cryptoKey)
        self.assertEqual(testAccountData.data, accountData[0].data)
        self.assertEqual(testAccountData.id, accountData[0].id)

    @patch("view.firststart.accounts.SetupAccountsWidget")
    @patch.object(ServiceHub, "getInstance")
    def test_invalidate_removes_all_accounts_and_shows_loading_icon_and_resets_network_service(self, mockGetInstance, fakeAccountsWidget):
        testAccountData = AccountData(AccountTypes.Dropbox, "fakeAccount", "sixteen byte key", {"apiToken": "fakeAPIToken"}, 1)
        self.fakeAccountsWidget.accounts = [testAccountData]
        fakeAccountsWidget.return_value = self.fakeAccountsWidget
        fakeHub = MagicMock()
        fakeHub.isNetworkServiceRunning.return_value = True
        mockGetInstance.return_value = fakeHub

        component = SetupAccountsWrapperWidget()

        self.assertEqual(len(component.getFormData()), len(self.fakeAccountsWidget.accounts))

        component.invalidate()

        self.assertEqual(self.fakeAccountsWidget.accounts, [])
        self.assertTrue(fakeHub.isNetworkServiceRunning.called)
        self.assertTrue(fakeHub.shutdownNetwork.called)
        self.assertTrue(fakeHub.initNetworkService.called)
