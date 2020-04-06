from dataclasses import dataclass


@dataclass
class UnixPermission():
    hasRead: bool = False
    hasWrite: bool = False
    hasExecute: bool = False


class UnixFilesystemPermissionsObject():
    ownerPermissions = None
    groupPermissions = None
    otherPermissions = None

    group = None
    owner = None

    def __init__(self, cliString):
        splitted = cliString.split(" ")
        self.ownerPermissions = self._getPermissions(splitted[0][1:4])
        self.groupPermissions = self._getPermissions(splitted[0][4:7])
        self.otherPermissions = self._getPermissions(splitted[0][7:])

        self.owner = splitted[2]
        self.group = splitted[3]

    def _getPermissions(self, permissionString):
        hasRead = permissionString[0] == "r"
        hasWrite = permissionString[1] == "w"
        hasExecute = permissionString[2] == "x"

        return UnixPermission(hasRead, hasWrite, hasExecute)


class UnixUserGroupMembershipsObject():
    memberships = None

    def __init__(self, cliString):
        splitted = cliString.split(" : ")
        self.memberships = [member for member in splitted[1].replace("\n", "").split(" ")]


class InvalidWorkspacePermissionException(Exception):
    pass


class WorkspacePermissionValidator():

    def __init__(self, username, path, permissionCLIString, membershipCLIString):
        self.__username = username
        self.__path = path
        self.__permissionCLIString = permissionCLIString
        self.__membershipCLIString = membershipCLIString

    def validate(self):
        permissionObject = UnixFilesystemPermissionsObject(self.__permissionCLIString)
        membershipObject = UnixUserGroupMembershipsObject(self.__membershipCLIString)

        userIsOwner = permissionObject.owner == self.__username
        ownerCanOperate = permissionObject.ownerPermissions.hasRead and permissionObject.ownerPermissions.hasWrite

        userInGroup = self.__username in membershipObject.memberships
        groupCanOperate = permissionObject.groupPermissions.hasRead and permissionObject.groupPermissions.hasWrite

        otherCanOperate = permissionObject.otherPermissions.hasRead and permissionObject.otherPermissions.hasWrite

        validWorkspace = userIsOwner and ownerCanOperate or userInGroup and groupCanOperate or otherCanOperate

        if not validWorkspace:
            raise InvalidWorkspacePermissionException(f"User '{self.__username}' has no read and write permissions for remote workspace '{self.__path}'. Please provide read and write permissions.'")
