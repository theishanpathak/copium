"""Stopgap relevance gate: checks whether a Job Apps message arrived recently.

Gmail's watch() fires on ANY mailbox change, not just Job Apps changes, since
history tracking is mailbox-wide. This script is a temporary filter run as the
first CI step -- it prints "true" or "false" to stdout so the workflow can
skip the rest of the pipeline when nothing Job-Apps-relevant actually happened.

This is NOT the fully correct fix (that requires tracking the last-processed
historyId and diffing against it via history.list(), which belongs in
Phase 10 once Supabase is wired up for state). This is just good enough to
stop wasted Action runs today.
"""

import sys
from datetime import datetime, timedelta, timezone

from copium.gmail_auth import JOB_APPS_LABEL_ID, get_gmail_service


def has_recent_job_apps_message(minutes: int = 5) -> bool:
    """Check whether the most recent Job Apps message arrived within the last N minutes.

    Args:
        minutes: how far back to consider a message "recent."

    Returns:
        bool: True if a Job Apps message arrived within the window, False otherwise.
    """
    service = get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=[JOB_APPS_LABEL_ID], maxResults=1)
        .execute()
    )
    messages = results.get("messages", [])
    if not messages:
        return False

    most_recent = (
        service.users()
        .messages()
        .get(userId="me", id=messages[0]["id"], format="metadata")
        .execute()
    )
    internal_date_ms = int(most_recent["internalDate"])
    message_time = datetime.fromtimestamp(internal_date_ms / 1000, tz=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    return message_time > cutoff


if __name__ == "__main__":
    is_relevant = has_recent_job_apps_message()
    print("true" if is_relevant else "false", file=sys.stdout)