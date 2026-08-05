"""One-off call to start Gmail push notifications for the Job Apps label."""
from copium.gmail_auth import JOB_APPS_LABEL_ID, get_gmail_service

PROJECT_ID = "copium-504602"
TOPIC_NAME = "gmail-job-apps"

def start_watch() -> dict:
    """Register a Gmail watch on the Job Apps label, pushing to the Pub/Sub topic."""

    service = get_gmail_service()
    request_body = {
        "labelIds": [JOB_APPS_LABEL_ID],
        "topicName": f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}",
    }

    return service.users().watch(userId="me", body=request_body).execute()



if __name__ == "__main__":
    response = start_watch()
    print(response)

