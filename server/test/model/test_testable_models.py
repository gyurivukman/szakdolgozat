import unittest

import logging

from uuid import uuid4

from model.message import NetworkMessage, MessageTypes, NetworkMessageFormatError


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
