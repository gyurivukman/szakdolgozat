import unittest
import logging

from uuid import uuid4

import model.task

from model.message import NetworkMessage, MessageTypes, NetworkMessageFormatError
from model.config import AccountData, AccountTypes
from model.file import FileData, FileStatuses
from model.permission import WorkspacePermissionValidator, InvalidWorkspacePermissionException
from model.task import FileTask
from model.wizard import WIZARD_PROGRESS_STATES


logging.disable(logging.CRITICAL)


class NetworkMessageBuilderSunnyTests(unittest.TestCase):

    def test_builder_builds_with_passed_parameters(self):
        messageType = MessageTypes.UPLOAD_FILE
        testUUID = uuid4().hex
        testData = {"testValue": "testKey"}

        builder = NetworkMessage.Builder(MessageTypes.UPLOAD_FILE)
        message = builder.withUUID(testUUID).withData(testData).build()

        self.assertEqual(message.header.messageType, messageType)
        self.assertEqual(message.data, testData)

    def test_builder_can_generate_random_32_byte_uuid(self):
        messageType = MessageTypes.UPLOAD_FILE
        testData = {"testValue": "testKey"}

        builder = NetworkMessage.Builder(MessageTypes.UPLOAD_FILE)
        message = builder.withRandomUUID().withData(testData).build()

        self.assertIsNotNone(message.header.uuid)
        self.assertEqual(len(message.header.uuid), 32)
        self.assertEqual(str, type(message.header.uuid))

    def test_builder_generated_uuid_is_random(self):
        messageType = MessageTypes.UPLOAD_FILE
        testData = {"testValue": "testKey"}

        builder = NetworkMessage.Builder(MessageTypes.UPLOAD_FILE)
        message1 = builder.withRandomUUID().withData(testData).build()
        message2 = builder.withRandomUUID().withData(testData).build()

        self.assertIsNotNone(message1.header.uuid)
        self.assertIsNotNone(message2.header.uuid)

        self.assertEqual(len(message1.header.uuid), 32)
        self.assertEqual(len(message2.header.uuid), 32)

        self.assertEqual(str, type(message1.header.uuid))
        self.assertEqual(str, type(message2.header.uuid))

        self.assertNotEqual(message1.header.uuid, message2.header.uuid)

    def test_uuid_and_data_are_not_required(self):
        messageType = MessageTypes.GET_WORKSPACE

        message = NetworkMessage.Builder(messageType).build()

        self.assertEqual(message.header.messageType, messageType)
        self.assertIsNone(message.header.uuid)
        self.assertIsNone(message.data)


class NetworkMessageBuilderRainyTests(unittest.TestCase):

    def test_invalid_message_type(self):
        builder = NetworkMessage.Builder("asd")

        with self.assertRaises(ValueError):
            builder.build()


class NetworkMessageRainyTests(unittest.TestCase):

    def test_invalid_type_for_constructor_argument(self):
        try:
            NetworkMessage("")
            self.fail("NetworkMessageRainyTests.test_invalid_type_for_constructor_argument passed for non-dict constructor type!")
        except NetworkMessageFormatError as e:
            self.assertEqual(str(e), "Invalid network message format! Passed argument must be a dict!")

    def test_missing_header_key_in_constructor_argment(self):
        try:
            NetworkMessage({})
            self.fail("NetworkMessageRainyTests.test_missing_header_key_in_constructor_argment passed for argument {}")
        except NetworkMessageFormatError as e:
            self.assertEqual(str(e), "Invalid network message format! Passed dict must contain key: 'header'!")

    def test_invalid_header_data_in_constructor_argument_wrong_type(self):
        try:
            NetworkMessage({"header": "invalidType"})
            self.fail("NetworkMessageRainyTests.test_invalid_header_data_in_constructor_argument_wrong_type passed for invalid 'header' key: {'header':'invalidType'}")
        except NetworkMessageFormatError as e:
            self.assertEqual(str(e), "Invalid argument for NetworkMessageHeader: must be dict, received <class 'str'> instead!")

    def test_invalid_header_data_in_constructor_argument_empty_dict(self):
        try:
            NetworkMessage({"header": {}})
            self.fail("NetworkMessageRainyTests.test_invalid_header_data_in_constructor_argument_empty_dict passed for invalid 'header' key: {'header':{}}")
        except NetworkMessageFormatError as e:
            self.assertEqual(str(e), "Invalid header format, missing key: messageType")

    def test_invalid_header_data_uuid_wrong_type(self):
        try:
            NetworkMessage({"header": {"messageType": MessageTypes.GET_WORKSPACE, "uuid": 5}})
            self.fail("NetworkMessageRainyTests.test_invalid_header_data_uuid_wrong_type passed for invalid 'header' key: {'header': {'messageType': MessageTypes.GET_WORKSPACE, 'uuid': 5}}")
        except NetworkMessageFormatError as e:
            self.assertEqual(str(e), "Invalid header format, key 'uuid' must be of type str. Received <class 'int'> instead.")

    def test_invalid_header_data_uuid_wrong_length(self):
        try:
            invalidLengthUUID = "wrongLenghtUUID"
            NetworkMessage({"header": {"messageType": MessageTypes.GET_WORKSPACE, "uuid": invalidLengthUUID}})
            self.fail(f"NetworkMessageRainyTests.test_invalid_header_data_uuid_wrong_length passed for invalid length 'uuid' key in 'header': '{invalidLengthUUID}'")
        except NetworkMessageFormatError as e:
            self.assertEqual(str(e), f"Invalid header format, key 'uuid' must be of type str with a length of 32. Received length: {len(invalidLengthUUID)}")


class AccountDataTests(unittest.TestCase):

    def test_serialize_returns_dict_with_passed_values(self):
        expectedData = {'id': None, 'accountType': AccountTypes.Dropbox, 'identifier': 'MyIdentifier', 'cryptoKey': 'sixteen byte key', 'data': {"myDataKey": "myDataValue"}}

        testAccount = AccountData(**expectedData)
        serialized = testAccount.serialize()

        self.assertEqual(type(serialized), dict)
        self.assertEqual(serialized, expectedData)


class FileDataTests(unittest.TestCase):

    def test_serialize_returns_dict_with_passed_values(self):
        expectedData = {"filename": "testFile", "modified": 1234, "size": 5678, "path": "somePath", "fullPath": "somePath/testFile"}

        testFileData = FileData(**expectedData)
        serialized = testFileData.serialize()

        self.assertEqual(type(serialized), dict)
        self.assertEqual(serialized, expectedData)


class WorkspacePermissionValidatorSunnyTests(unittest.TestCase):

    def test_user_is_owner_and_owner_has_read_and_write_permissions(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwxrwxr-x 4 testuser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : testgroup adm cdrom sudo dip plugdev lpadmin sambashare"
        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
        except InvalidWorkspacePermissionException as e:
            self.fail(f"WorkspacePermissionValidator raised an exception for a valid test scenario: {str(e)}")

    def test_user_is_not_owner_but_in_group_and_group_has_read_and_write_permissions(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwxrwxr-x 4 otherUser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : testgroup adm cdrom sudo dip plugdev lpadmin sambashare"
        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
        except InvalidWorkspacePermissionException as e:
            self.fail(f"WorkspacePermissionValidator raised an exception for a valid test scenario: {str(e)}")

    def test_user_is_not_owner_and_not_in_group_but_other_has_read_and_write_permissions(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwxrwxrwx 4 otherUser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
        except InvalidWorkspacePermissionException as e:
            self.fail(f"WorkspacePermissionValidator raised an exception for a valid test scenario: {str(e)}")


class WorkspacePermissionValidatorRainyTests(unittest.TestCase):

    def test_user_is_owner_but_has_no_read_nor_write_permission(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "d--x------ 4 testuser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is owner but without read and write permissions!")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_owner_but_has_no_read_permission(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "d-wx------ 4 testuser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is owner but without read permission!")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_owner_but_has_no_write_permission(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "dr-x------ 4 testuser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is owner but without write permission!")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_in_group_but_group_has_no_read_nor_write_permissions(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwx------ 4 otheruser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm testgroup cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is in the group, but the group has no permissions!")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_in_group_but_group_has_no_read_permission(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwx-w---- 4 otheruser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm testgroup cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is in the group, but the group has no read permission!")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_in_group_but_group_has_no_write_permission(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwxr----- 4 otheruser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm testgroup cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is in the group, but the group has no write permission!")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_neither_owner_nor_in_group_and_other_has_no_read_nor_write_permissions(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwx------ 4 otheruser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm testgroup cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is neither the owner, nor is in the group, and other has no permissions")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_neither_owner_nor_in_group_and_other_has_no_read_permission(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwx----w- 4 otheruser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm testgroup cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is neither the owner, nor is in the group, and other has no read permission")
        except InvalidWorkspacePermissionException as e:
            pass

    def test_user_is_neither_owner_nor_in_group_and_other_has_no_write_permission(self):
        username = "testuser"
        path = "testPath"

        permissionCLIString = "drwx---r-- 4 otheruser testgroup 4096 march 16 11:37 testPath"
        groupCLIString = "testuser : adm testgroup cdrom sudo dip plugdev lpadmin sambashare"

        validator = WorkspacePermissionValidator(username, path, permissionCLIString, groupCLIString)
        try:
            validator.validate()
            self.fail(f"WorkspacePermissionValidator failed to raise an exception when the user is neither the owner, nor is in the group, and other has no write permission")
        except InvalidWorkspacePermissionException as e:
            pass


class TaskArchiveTests(unittest.TestCase):

    def setUp(self):
        self.taskArchive = model.task.TaskArchive()
        self.taskArchive.clearAllTasks()

    def test_task_is_added(self):
        task = FileTask(uuid="testUUID", taskType=FileStatuses.UPLOADING_TO_CLOUD, subject="testSubject")
        self.taskArchive.addTask("myTaskKey", task)

        addedTask = self.taskArchive.getTask("myTaskKey")

        self.assertIsNotNone(addedTask)
        self.assertEqual(type(addedTask), FileTask)
        self.assertEqual(task.uuid, addedTask.uuid)
        self.assertEqual(task.taskType, addedTask.taskType)
        self.assertEqual(task.subject, addedTask.subject)
        self.assertEqual(task.stale, False)

    def test_task_is_removed(self):
        task = FileTask(uuid="testUUID", taskType=FileStatuses.UPLOADING_TO_CLOUD, subject="testSubject")
        self.taskArchive.addTask("myTaskKey", task)
        self.taskArchive.removeTask("myTaskKey")

        self.assertIsNone(self.taskArchive.getTask("myTaskKey"))

    def test_task_is_overridden(self):
        oldTask = FileTask(uuid="testUUID", taskType=FileStatuses.DOWNLOADING_FROM_CLOUD, subject="oldtestSubject")
        newTask = FileTask(uuid="newtestUUID", taskType=FileStatuses.UPLOADING_TO_CLOUD, subject="newtestSubject")

        self.taskArchive.addTask("myTaskKey", oldTask)
        self.taskArchive.addTask("myTaskKey", newTask)

        addedTask = self.taskArchive.getTask("myTaskKey")

        self.assertIsNotNone(addedTask)
        self.assertEqual(type(addedTask), FileTask)
        self.assertEqual(newTask.uuid, addedTask.uuid)
        self.assertEqual(newTask.taskType, addedTask.taskType)
        self.assertEqual(newTask.subject, addedTask.subject)

    def test_task_is_cancelled(self):
        task = FileTask(uuid="testUUID", taskType=FileStatuses.UPLOADING_TO_CLOUD, subject="testSubject")
        self.taskArchive.addTask("myTaskKey", task)
        self.taskArchive.cancelTask("myTaskKey")

        addedTask = self.taskArchive.getTask("myTaskKey")

        self.assertIsNotNone(addedTask)
        self.assertEqual(addedTask.stale, True)

    def test_gettask_returns_none_for_nonexisting_task(self):
        nonexisting = self.taskArchive.getTask("nonexisting")
        self.assertIsNone(nonexisting)

    def test_removeTask_does_not_raise_exception_for_nonexisting_task_removal(self):
        try:
            self.taskArchive.removeTask("nonexisting")
        except Exception as e:
            self.fail("TaskArchive raised an exception when attempting to remove a nonexisting task! It should not!")

    def test_cancelTask_does_not_raise_exception_for_nonexisting_task_cancellation(self):
        try:
            self.taskArchive.cancelTask("nonexisting")
        except Exception as e:
            self.fail("TaskArchive raised an exception when attempting to cancel a nonexisting task! It should not!")


class WizardProgressStatesTests(unittest.TestCase):

    def test_state_order_for_going_foward(self):
        forwardStates = [WIZARD_PROGRESS_STATES.NETWORK, WIZARD_PROGRESS_STATES.ACCOUNTS, WIZARD_PROGRESS_STATES.SUMMARY]
        state = WIZARD_PROGRESS_STATES.WELCOME

        for fwState in forwardStates:
            state = state.next()
            self.assertEqual(state, fwState)

    def test_state_order_for_going_backwards(self):
        backwardStates = [WIZARD_PROGRESS_STATES.ACCOUNTS, WIZARD_PROGRESS_STATES.NETWORK, WIZARD_PROGRESS_STATES.WELCOME]
        state = WIZARD_PROGRESS_STATES.SUMMARY

        for bwState in backwardStates:
            state = state.previous()
            self.assertEqual(state, bwState)

    def test_summary_is_the_last_state(self):
        state = WIZARD_PROGRESS_STATES.SUMMARY
        try:
            state.next()
            self.fail("SUMMARY should be the last state and calling next on it must raise a value error!")
        except ValueError as e:
            self.assertEqual(str(e), "Enumeration ended")

    def test_welcome_is_the_first_state(self):
        state = WIZARD_PROGRESS_STATES.WELCOME
        try:
            state.previous()
            self.fail("WELCOME should be the first state and calling previous on it must raise a value error!")
        except ValueError as e:
            self.assertEqual(str(e), "Enumeration ended")

    def test_state_display_values_are_correct(self):
        displayValues = ['Welcome', 'Network &\nDirectory', 'Accounts', 'Summary']
        state = WIZARD_PROGRESS_STATES.WELCOME

        for dpValue, stateIndex in zip(displayValues, range(3)):
            self.assertEqual(state.toDisplayValue(), dpValue)
            if stateIndex < 3:
                state = state.next()


if __name__ == '__main__':
    unittest.main()
