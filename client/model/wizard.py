from enum import IntEnum


class WIZARD_PROGRESS_STATES(IntEnum):
    WELCOME = 0
    NETWORK = 1
    ACCOUNTS = 2
    SUMMARY = 3

    def next(self):
        if self.value == 3:
            raise ValueError('Enumeration ended')
        return WIZARD_PROGRESS_STATES(self.value + 1)

    def previous(self):
        if self.value == 0:
            raise ValueError('Enumeration ended')
        return WIZARD_PROGRESS_STATES(self.value - 1)

    def toDisplayValue(self):
        ENUM_DISPLAY_VALUES = ['Welcome', 'Network &\nDirectory', 'Accounts', 'Summary']
        return ENUM_DISPLAY_VALUES[self.value]
