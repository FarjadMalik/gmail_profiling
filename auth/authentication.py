import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = 'auth/token.pickle'
CREDENTIALS_PATH = 'auth/credentials.json'


def get_gmail_service():
    """
    Authenticate and create a Gmail API service client.

    Returns:
        googleapiclient.discovery.Resource: Gmail API service instance.
    """
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token_file:
            creds = pickle.load(token_file)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'wb') as token_file:
            pickle.dump(creds, token_file)

    return build('gmail', 'v1', credentials=creds)
