

class AuthenticationController(object):
    def login(self, uname, pwd):
        return uname=="admin" and pwd =="admin"