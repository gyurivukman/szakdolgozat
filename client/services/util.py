import requests
import time
import jwt


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class InvalidAccountCredentialsException(Exception):
    pass


class AccountDuplicationError(Exception):
    pass


class DropboxAccountTester():

    def __init__(self, accountData):
        self.__token = accountData.data["apiToken"]
        self.__url = "https://api.dropboxapi.com/2/users/get_current_account"

    def validate(self):
        headers = {"Authorization": f"Bearer {self.__token}"}
        res = requests.post(url=self.__url, headers=headers)
        if res.status_code != 200:
            raise InvalidAccountCredentialsException("Invalid API Token! Please provide a valid Dropbox API token.")


class DriveAccountTester():

    def __init__(self, accountData):
        self.__creds = accountData.data

    def validate(self):
        validityResult = {"isValid":True, "message": ""}

        iat = time.time()
        exp = iat + 3600

        payload = {
            "iss": self.__creds["client_email"],
            "scope": "https://www.googleapis.com/auth/drive",
            "aud": "https://oauth2.googleapis.com/token",
            "iat": iat,
            "exp": exp
        }

        privateKey = self.__creds["private_key"]
        signedJwt = jwt.encode(payload, privateKey, algorithm='RS256')

        urlParams = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signedJwt
        }

        try:
            tokenRes = requests.post(url="https://oauth2.googleapis.com/token", params=urlParams)
            tokenRes.raise_for_status()
        except requests.exceptions.HTTPError:
            raise InvalidAccountCredentialsException("Invalid Google Drive account credentials! Please review the provided json file.")
