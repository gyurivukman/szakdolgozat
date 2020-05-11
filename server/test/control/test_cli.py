import unittest

from unittest.mock import patch
from argparse import ArgumentTypeError

from control.cli import AESKeyArgumentValidator, WorkspaceArgumentValidator, CreateWorkspaceAction


class TestAESKeyArgumentValidator(unittest.TestCase):

    def test_16_byte_long_string_is_valid(self):
        try:
            testKey = "sixteen byte key"
            AESKeyArgumentValidator.validate(testKey)
        except ArgumentTypeError:
            self.fail("AESKeyArgumentValidator.validate raised ArgumentTypeError for a valid key: 'sixteen byte key'!")

    def test_empty_string_is_invalid(self):
        try:
            testKey = ""
            AESKeyArgumentValidator.validate(testKey)
            self.fail("AESKeyArgumentValidator.validate failed to raise ArgumentTypeError for an invalid key: ''!")
        except ArgumentTypeError:
            pass

    def test_smaller_than_16_byte_string_is_invalid(self):
        try:
            testKey = "small"
            AESKeyArgumentValidator.validate(testKey)
            self.fail("AESKeyArgumentValidator.validate failed to raise ArgumentTypeError for an invalid key: 'small'!")
        except ArgumentTypeError:
            pass

    def test_longer_than_16_byte_string_is_invalid(self):
        try:
            testKey = "iamaveryverylongaeskeyishouldbeinvalid"
            AESKeyArgumentValidator.validate(testKey)
            self.fail("AESKeyArgumentValidator.validate failed to raise ArgumentTypeError for an invalid key: 'iamaveryverylongaeskeyishouldbeinvalid'!")
        except ArgumentTypeError:
            pass

    def test_not_str_is_invalid(self):
        try:
            testKey = 5
            AESKeyArgumentValidator.validate(testKey)
            self.fail("AESKeyArgumentValidator.validate failed to raise ArgumentTypeError for an invalid key: '5' of type 'int'!")
        except ArgumentTypeError:
            pass


class TestWorkspaceArgumentValidator(unittest.TestCase):

    @patch("os.access")
    @patch("os.path.isdir")
    def test_dir_with_read_and_write_permissions_is_valid(self, isdirMock, accessMock):
        isdirMock.return_value = True
        accessMock.side_effect = [True, True]

        testDirPath = "testDirPath"
        try:
            WorkspaceArgumentValidator.validate(testDirPath)
        except ArgumentTypeError:
            self.fail("WorkspaceArgumentValidator.validate raised an ArgumentTypeError for a valid directory!")

        self.assertEqual(isdirMock.call_count, 1)
        self.assertEqual(isdirMock.call_args[0][0], testDirPath)

    @patch("os.access")
    @patch("os.path.isdir")
    def test_not_a_dir_is_invalid(self, isdirMock, accessMock):
        isdirMock.return_value = False
        accessMock.side_effect = [True, True]
        testDirPath = "testFilePath"
        try:
            WorkspaceArgumentValidator.validate(testDirPath)
            self.fail("WorkspaceArgumentValidator.validate failed to raise an ArgumentTypeError when the given filePath is not a directory!")
        except ArgumentTypeError:
            pass

    @patch("os.access")
    @patch("os.path.isdir")
    def test_dir_with_read_but_no_write_permissions_is_invalid(self, isdirMock, accessMock):
        isdirMock.return_value = True
        accessMock.side_effect = [True, False]
        testDirPath = "testDirPath"
        try:
            WorkspaceArgumentValidator.validate(testDirPath)
            self.fail("WorkspaceArgumentValidator.validate failed to raise an ArgumentTypeError when the given directory has no write access!")
        except ArgumentTypeError:
            pass

    @patch("os.access")
    @patch("os.path.isdir")
    def test_dir_with_write_but_no_read_permissions_is_invalid(self, isdirMock, accessMock):
        isdirMock.return_value = True
        accessMock.side_effect = [False, True]
        testDirPath = "testDirPath"
        try:
            WorkspaceArgumentValidator.validate(testDirPath)
            self.fail("WorkspaceArgumentValidator.validate failed to raise an ArgumentTypeError when the given directory has no read access!")
        except ArgumentTypeError:
            pass

    @patch("os.access")
    @patch("os.path.isdir")
    def test_dir_argument_is_not_a_string(self, isdirMock, accessMock):
        isdirMock.return_value = True
        accessMock.side_effect = [True, False]
        testDirPath = 5
        try:
            WorkspaceArgumentValidator.validate(testDirPath)
            self.fail("WorkspaceArgumentValidator.validate failed to raise an ArgumentTypeError when the argument is not string. It was '5', an integer.")
        except ArgumentTypeError:
            pass


class FakeNameSpace:
    pass


class TestCreateWorkspaceAction(unittest.TestCase):

    @patch("os.chmod")
    @patch("os.mkdir")
    def test_creates_workspace_and_server_directory(self, mkdirMock, chmodMock):
        action = CreateWorkspaceAction(None, "testDirPath")
        action(None, FakeNameSpace(), "testDirPath")

        self.assertEqual(mkdirMock.call_count, 2)
        self.assertEqual(mkdirMock.call_args_list[0].args[0], "testDirPath/server")
        self.assertEqual(mkdirMock.call_args_list[1].args[0], "testDirPath/client")

        self.assertEqual(chmodMock.call_count, 2)
        self.assertEqual(chmodMock.call_args_list[0].args[0], "testDirPath/server")
        self.assertEqual(chmodMock.call_args_list[0].args[1], 511)

        self.assertEqual(chmodMock.call_args_list[1].args[0], "testDirPath/client")
        self.assertEqual(chmodMock.call_args_list[1].args[1], 511)

    @patch("shutil.rmtree")
    @patch("os.chmod")
    @patch("os.mkdir")
    def test_cleans_and_recreates_server_directory_if_workspace_already_exists(self, mkdirMock, chmodMock, rmtreeMock):
        mkdirMock.side_effect = [FileExistsError, None, None]
        action = CreateWorkspaceAction(None, "testDirPath")
        action(None, FakeNameSpace(), "testDirPath")

        self.assertEqual(mkdirMock.call_count, 3)
        self.assertEqual(mkdirMock.call_args_list[0].args[0], "testDirPath/server")
        self.assertEqual(mkdirMock.call_args_list[1].args[0], "testDirPath/server")

        self.assertEqual(rmtreeMock.call_count, 1)
        self.assertEqual(rmtreeMock.call_args[0][0], "testDirPath/server")

        self.assertEqual(chmodMock.call_count, 2)
        self.assertEqual(chmodMock.call_args_list[0].args[0], "testDirPath/server")
        self.assertEqual(chmodMock.call_args_list[0].args[1], 511)

        self.assertEqual(chmodMock.call_args_list[1].args[0], "testDirPath/client")
        self.assertEqual(chmodMock.call_args_list[1].args[1], 511)

    @patch("shutil.rmtree")
    @patch("os.chmod")
    @patch("os.mkdir")
    def test_leaves_client_directory_alone_if_it_already_exists(self, mkdirMock, chmodMock, rmtreeMock):
        mkdirMock.side_effect = [FileExistsError, None, FileExistsError]
        action = CreateWorkspaceAction(None, "testDirPath")
        action(None, FakeNameSpace(), "testDirPath")

        self.assertEqual(mkdirMock.call_count, 3)
