from __future__ import print_function
import pickle
import json
import os.path
from googleapiclient.discovery import build, MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'serviceaccount.json'

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES).with_subject('cryptstorepiserver@cryptstorepi.iam.gserviceaccount.com')

file_metadata = {'name': 'roka.png', 'parents':['12K0m_PA0tGhrunSBVGbxzCriTU6bMtjT']}
# media = MediaFileUpload('roka.png', mimetype='image/png', resumable=True, chunksize=262144)
service = build('drive', 'v3',credentials=creds)

# request = service.files().create(body=file_metadata, media_body=media, fields="*")
# response = None
# while response is None:
#     print("uploading chunk...")
#     status, response = request.next_chunk()
#     print(f"status: {status}")
# print(response)

# file_id = request.execute()
# print(f"id: {file_id}")
response = service.files().list(q="parents in '12K0m_PA0tGhrunSBVGbxzCriTU6bMtjT' and name contains '.png'").execute()
for i in response['files']:
    print(i)
# file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
# print(f'File ID: {file.get("id")}')
#13ClZDSLEl5YO5JHztTwZ_-jW0lQnUNXs
#File ID: 1QxDSGh6OARz0jgUEazxgw8tZVynZuD9h