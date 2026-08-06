"""Stopgap relevance gate: finds Job Apps messages that arrived recently.

Gmail's watch() fires on ANY mailbox change, not just Job Apps changes, since
history tracking is mailbox-wide. This script is a temporary filter run as the
first CI step -- it prints the id of every recent Job Apps message, one per
line, so the workflow can skip the rest of the pipeline when the output is
empty and otherwise knows exactly which messages to process.

This is NOT the fully correct fix (that requires tracking the last-processed
historyId and diffing against it via history.list(), which belongs in Phase 10
once Supabase is wired up for state). The interface is the permanent part: this
step's job is to answer "which messages should the pipeline handle," and the
Phase 10 version will answer it properly without changing what consumes it.
"""

from datetime import datetime, timedelta, timezone

from copium.gmail_auth import JOB_APPS_LABEL_ID, get_gmail_service

WINDOW_MINUTES = 5
SCAN_LIMIT = 10


def recent_job_apps_messages(minutes: int = WINDOW_MINUTES) -> list[str]:
    """Return the ids of Job Apps messages that arrived within the last N minutes.

    Checks several recent messages rather than only the newest, because two
    rejections can land seconds apart and a single-message check would silently
    drop all but the last one.

    Args:
        minutes: how far back to consider a message "recent."

    Returns:
        Message ids, newest first. Empty when nothing relevant arrived.
    """
    service = get_gmail_service()
    listing = (
        service.users()
        .messages()
        .list(userId="me", labelIds=[JOB_APPS_LABEL_ID], maxResults=SCAN_LIMIT)
        .execute()
    )

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    recent: list[str] = []

    for stub in listing.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(userId="me", id=stub["id"], format="metadata")
            .execute()
        )
        arrived = datetime.fromtimestamp(
            int(message["internalDate"]) / 1000, tz=timezone.utc
        )

        if arrived <= cutoff:
            # Gmail returns newest first, so everything after this is older too.
            break

        recent.append(stub["id"])

    return recent


if __name__ == "__main__":
    for message_id in recent_job_apps_messages():
        print(message_id)