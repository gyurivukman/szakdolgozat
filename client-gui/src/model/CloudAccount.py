

class CloudAccount(object):
    def __init__(self, id, accType, username, password):
        self. id = id
        self.accType = accType
        self.username = username
        self.password = password

    def __repr__(self):
        return "Dropbox/{}".format(self.username)

