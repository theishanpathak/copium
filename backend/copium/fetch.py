"""Fetches a Gmail message by ID and parses it into plain text."""

from googleapiclient.discovery import Resource
from copium.email_parse import extract_body, extract_headers


def fetch_email(service: Resource, message_id: str) -> dict[str, str]:
    """Fetch a Gmail message by ID and parse it into subject/sender/date/body."""
    message = (
        service.users().messages().get(userId="me", id=message_id, format="full").execute()
    )
    headers = extract_headers(message["payload"])

    return {
        "subject": headers.get("Subject", ""),
        "sender": headers.get("From", ""),
        "received_at": headers.get("Date", ""),
        "body": extract_body(message["payload"]),
    }
