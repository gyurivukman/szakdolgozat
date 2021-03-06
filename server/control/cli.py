import stat
import os
import shutil

from argparse import ArgumentTypeError, Action


CONSOLE_ARGUMENTS = None


class ArgumentValidator():

    @staticmethod
    def validate(value):
        pass


class AESKeyArgumentValidator(ArgumentValidator):

    @staticmethod
    def validate(value):
        internalValue = None
        if type(value) is not str:
            raise ArgumentTypeError("invalid type for --key! Value of --key must be a 16 character long string!")
        internalValue = str(value)

        if len(internalValue) != 16:
            raise ArgumentTypeError("invalid length for --key! Value of --key must be a 16 character long string!")
        return internalValue


class WorkspaceArgumentValidator(ArgumentValidator):

    @staticmethod
    def validate(value):
        internalValue = None
        if type(value) is not str:
            raise ArgumentTypeError("Invalid type for --workspace! Value of --workspace must be a valid (absolute or relative) existing path with read and write permissions.")

        internalValue = str(value)
        if os.path.isdir(internalValue):
            if not os.access(internalValue, os.R_OK):
                raise ArgumentTypeError(f"No read permission for directory '{internalValue}'! Please provide read and write permissions for cryptstorepi server for that path.")
            elif not os.access(internalValue, os.W_OK):
                raise ArgumentTypeError(f"No read permission for directory '{internalValue}'! Please provide read and write permissions for cryptstorepi server for that path.")
        else:
            raise ArgumentTypeError(f"'{internalValue}' is not a directory! Value of --workspace must be a valid (absolute or relative) existing path with read and write permissions.")

        return internalValue


class CreateWorkspaceAction(Action):
    __WORKSPACE_PERMISSIONS = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed!")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, value)
        path = value.rstrip("/", 1) if value[-1] == "/" else value
        self.__createServerWorkspace(path)
        self.__createClientWorkspace(path)

    def __createServerWorkspace(self, workspacePath):
        path = f"{workspacePath}/server"
        try:
            os.mkdir(path)
        except FileExistsError:
            shutil.rmtree(path)
            os.mkdir(path)
        os.chmod(path, self.__WORKSPACE_PERMISSIONS)

    def __createClientWorkspace(self, workspacePath):
        path = f"{workspacePath}/client"
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        os.chmod(path, self.__WORKSPACE_PERMISSIONS)
