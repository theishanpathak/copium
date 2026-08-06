"""Register and renew Gmail push notifications for the Job Apps label."""

from datetime import datetime, timezone
from typing import Any
from copium.gmail_auth import JOB_APPS_LABEL_ID, get_gmail_service

PROJECT_ID = "copium-504602"
TOPIC_NAME = "gmail-job-apps"

def start_watch() -> dict[str, Any]:
    """Register a Gmail watch on the Job Apps label, pushing to the Pub/Sub topic."""

    service = get_gmail_service()
    request_body = {
        "labelIds": [JOB_APPS_LABEL_ID],
        "labelFilterBehavior": "INCLUDE",
        "topicName": f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}",
    }

    return service.users().watch(userId="me", body=request_body).execute()



def main() -> None:
    """Renew the Gmail push subscription and report the new expiry."""
    response = start_watch()

    expires_at = datetime.fromtimestamp(
        int(response["expiration"]) / 1000, tz=timezone.utc
    )
    remaining = expires_at - datetime.now(tz=timezone.utc)

    print(f"watch renewed | historyId={response['historyId']}")
    print(f"expires {expires_at:%Y-%m-%d %H:%M UTC} (in {remaining.days}d)")


if __name__ == "__main__":
    main()
