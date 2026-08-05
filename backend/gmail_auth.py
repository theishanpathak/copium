"""Gmail OAuth auth + message listing for the Job Apps label."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
JOB_APPS_LABEL_ID = "Label_2983195907014674210"


def get_gmail_service() -> Resource:
    """Authenticate with Gmail, reusing/refreshing a saved token when possible."""
    creds: Credentials | None = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def list_job_messages(service: Resource, max_results: int = 10) -> list[dict]:
    """Return message stubs (id + threadId) under the Job Apps label."""
    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=[JOB_APPS_LABEL_ID], maxResults=max_results)
        .execute()
    )
    return results.get("messages", [])


def get_subject(service: Resource, message_id: str) -> str:
    """Fetch a message and return its Subject header."""
    msg = service.users().messages().get(userId="me", id=message_id).execute()
    headers = msg["payload"]["headers"]
    return next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")


if __name__ == "__main__":
    service = get_gmail_service()
    messages = list_job_messages(service)
    print(f"Found {len(messages)} messages under Job Apps")
    for msg in messages:
        print(f"- {get_subject(service, msg['id'])}")