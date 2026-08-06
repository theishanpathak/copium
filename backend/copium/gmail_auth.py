"""Gmail OAuth auth + message listing for the Job Apps label."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


def _write_credentials_from_env() -> None:
    """Write client_secret.json/token.json from env vars, for CI where no local files exist."""
    client_secret_json = os.environ.get("GMAIL_CLIENT_SECRET_JSON")
    token_json = os.environ.get("GMAIL_TOKEN_JSON")
 
    if client_secret_json and not os.path.exists(CLIENT_SECRET_FILE):
        with open(CLIENT_SECRET_FILE, "w") as f:
            f.write(client_secret_json)
 
    if token_json and not os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "w") as f:
            f.write(token_json)

def get_gmail_service() -> Resource:
    """Authenticate with Gmail, reusing/refreshing a saved token when possible."""
    _write_credentials_from_env()
    creds: Credentials | None = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.valid:
        return build("gmail", "v1", credentials=creds)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    elif os.environ.get("CI"):
        raise RuntimeError(
            "Gmail credentials are unusable and no interactive login is possible "
            "in CI. Re-run the auth flow locally and update GMAIL_TOKEN_JSON."
        )
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)




