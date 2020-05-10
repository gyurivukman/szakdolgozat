import unittest
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QObject, pyqtSignal

from services.hub import ServiceHub
from view.firststart.accounts import SetupAccountsWrapperWidget, SetupAccountsWidget, DropboxAccountForm, DriveAccountForm
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


class TestDropboxAccountForm(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.testAccountForm = DropboxAccountForm()

    def tearDown(self):
        self.app.deleteLater()
        self.app.quit()

    def test_setAccountData_sets_data(self):
        testAccountData = AccountData(**{"accountType": AccountTypes.Dropbox, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": {"apiToken": "testAPIToken"}, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        componentAccountData = self.testAccountForm.getAccountData()

        self.assertEqual(testAccountData.accountType, componentAccountData.accountType)
        self.assertEqual(testAccountData.identifier, componentAccountData.identifier)
        self.assertEqual(testAccountData.cryptoKey, componentAccountData.cryptoKey)
        self.assertEqual(testAccountData.data, componentAccountData.data)
        self.assertEqual(testAccountData.id, componentAccountData.id)

    def test_reset_clears_account_specific_data_and_only_that(self):
        testAccountData = AccountData(**{"accountType": AccountTypes.Dropbox, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": {"apiToken": "testAPIToken"}, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)
        self.testAccountForm.reset()

        componentAccountData = self.testAccountForm.getAccountData()

        self.assertEqual(componentAccountData.accountType, testAccountData.accountType)
        self.assertEqual(componentAccountData.identifier, "")
        self.assertEqual(componentAccountData.cryptoKey, "")
        self.assertEqual(componentAccountData.data, {"apiToken": ""})
        self.assertEqual(componentAccountData.id, testAccountData.id)

    def test_isFormValid_returns_true_on_valid_account_data(self):
        testAccountData = AccountData(**{"accountType": AccountTypes.Dropbox, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": {"apiToken": "testAPIToken"}, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertTrue(self.testAccountForm.isFormValid())

    def test_isFormValid_returns_false_on_missing_identifier(self):
        testAccountData = AccountData(**{"accountType": AccountTypes.Dropbox, "identifier": "", "cryptoKey": "sixteen byte key", "data": {"apiToken": "testAPIToken"}, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertFalse(self.testAccountForm.isFormValid())

    def test_isFormValid_returns_false_on_missing_cryptoKey(self):
        testAccountData = AccountData(**{"accountType": AccountTypes.Dropbox, "identifier": "testAccount", "cryptoKey": "", "data": {"apiToken": "testAPIToken"}, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertFalse(self.testAccountForm.isFormValid())

    def test_isFormValid_returns_false_on_missing_apiToken(self):
        testAccountData = AccountData(**{"accountType": AccountTypes.Dropbox, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": {"apiToken": ""}, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertFalse(self.testAccountForm.isFormValid())


class TestDriveAccountForm(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.testAccountForm = DriveAccountForm()

    def tearDown(self):
        self.app.deleteLater()
        self.app.quit()

    def test_setAccountData_sets_data(self):
        testAccountSpecificData = {
            "type": "service_account",
            "project_id": "testID",
            "private_key_id": "testPrivKeyID",
            "private_key": "testPrivKey",
            "client_email": "testEmail",
            "client_id": "testClientID",
            "auth_uri": "testAuthUri",
            "token_uri": "testTokenUri",
            "auth_provider_x509_cert_url": "testCertProviderUri",
            "client_x509_cert_url": "testCertUri"
        }

        testAccountData = AccountData(**{"accountType": AccountTypes.GoogleDrive, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": testAccountSpecificData, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        componentAccountData = self.testAccountForm.getAccountData()

        self.assertEqual(testAccountData.accountType, componentAccountData.accountType)
        self.assertEqual(testAccountData.identifier, componentAccountData.identifier)
        self.assertEqual(testAccountData.cryptoKey, componentAccountData.cryptoKey)
        self.assertEqual(testAccountData.data, componentAccountData.data)
        self.assertEqual(testAccountData.id, componentAccountData.id)

    def test_reset_clears_account_specific_data_and_only_that(self):
        testAccountSpecificData = {
            "type": "service_account",
            "project_id": "testID",
            "private_key_id": "testPrivKeyID",
            "private_key": "testPrivKey",
            "client_email": "testEmail",
            "client_id": "testClientID",
            "auth_uri": "testAuthUri",
            "token_uri": "testTokenUri",
            "auth_provider_x509_cert_url": "testCertProviderUri",
            "client_x509_cert_url": "testCertUri"
        }

        testAccountData = AccountData(**{"accountType": AccountTypes.GoogleDrive, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": testAccountSpecificData, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)
        self.testAccountForm.reset()

        componentAccountData = self.testAccountForm.getAccountData()
        self.assertEqual(componentAccountData.accountType, testAccountData.accountType)
        self.assertEqual(componentAccountData.identifier, "")
        self.assertEqual(componentAccountData.cryptoKey, "")
        self.assertEqual(componentAccountData.data, {})
        self.assertEqual(componentAccountData.id, testAccountData.id)

    def test_isFormValid_returns_true_on_valid_account_data(self):
        testAccountSpecificData = {
            "type": "service_account",
            "project_id": "testID",
            "private_key_id": "testPrivKeyID",
            "private_key": "testPrivKey",
            "client_email": "testEmail",
            "client_id": "testClientID",
            "auth_uri": "testAuthUri",
            "token_uri": "testTokenUri",
            "auth_provider_x509_cert_url": "testCertProviderUri",
            "client_x509_cert_url": "testCertUri"
        }

        testAccountData = AccountData(**{"accountType": AccountTypes.GoogleDrive, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": testAccountSpecificData, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertTrue(self.testAccountForm.isFormValid())

    def test_isFormValid_returns_false_on_missing_identifier(self):
        testAccountSpecificData = {
            "type": "service_account",
            "project_id": "testID",
            "private_key_id": "testPrivKeyID",
            "private_key": "testPrivKey",
            "client_email": "testEmail",
            "client_id": "testClientID",
            "auth_uri": "testAuthUri",
            "token_uri": "testTokenUri",
            "auth_provider_x509_cert_url": "testCertProviderUri",
            "client_x509_cert_url": "testCertUri"
        }

        testAccountData = AccountData(**{"accountType": AccountTypes.GoogleDrive, "identifier": "", "cryptoKey": "sixteen byte key", "data": testAccountSpecificData, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertFalse(self.testAccountForm.isFormValid())

    def test_isFormValid_returns_false_on_missing_cryptoKey(self):
        testAccountSpecificData = {
            "type": "service_account",
            "project_id": "testID",
            "private_key_id": "testPrivKeyID",
            "private_key": "testPrivKey",
            "client_email": "testEmail",
            "client_id": "testClientID",
            "auth_uri": "testAuthUri",
            "token_uri": "testTokenUri",
            "auth_provider_x509_cert_url": "testCertProviderUri",
            "client_x509_cert_url": "testCertUri"
        }

        testAccountData = AccountData(**{"accountType": AccountTypes.GoogleDrive, "identifier": "testAccount", "cryptoKey": "", "data": testAccountSpecificData, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertFalse(self.testAccountForm.isFormValid())

    def test_isFormValid_returns_false_on_missing_drive_credentials(self):
        testAccountData = AccountData(**{"accountType": AccountTypes.GoogleDrive, "identifier": "testAccount", "cryptoKey": "sixteen byte key", "data": {}, "id": 1})
        self.testAccountForm.setAccountData(testAccountData)

        self.assertFalse(self.testAccountForm.isFormValid())
