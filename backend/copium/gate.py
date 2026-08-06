"""Resolves which Gmail messages the pipeline should process.

Gmail's push notification only says the mailbox changed, never which message
arrived. This module answers that question, preferring a historyId diff against
the stored cursor and falling back to a recency window when no usable cursor
exists.
"""

from datetime import datetime, timedelta, timezone

from googleapiclient.errors import HttpError

from copium.config.settings import settings
from copium.storage.queries import get_cursor

WINDOW_MINUTES = 5
SCAN_LIMIT = 10


def _from_history(service, start_history_id: int) -> tuple[list[str], int] | None:
    """Diff the mailbox since start_history_id for added Job Apps messages.

    Returns:
        (message ids, newest historyId), or None if the cursor is too old for
        Gmail to serve, which happens after roughly a week.
    """
    message_ids: list[str] = []
    newest = start_history_id
    page_token = None

    try:
        while True:
            response = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=str(start_history_id),
                    labelId=settings.JOB_APPS_LABEL_ID,
                    historyTypes=["messageAdded"],
                    pageToken=page_token,
                )
                .execute()
            )

            for record in response.get("history", []):
                newest = max(newest, int(record["id"]))
                for added in record.get("messagesAdded", []):
                    message = added["message"]
                    if settings.JOB_APPS_LABEL_ID in message.get("labelIds", []):
                        message_ids.append(message["id"])

            newest = max(newest, int(response.get("historyId", newest)))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

    except HttpError as exc:
        if exc.resp.status == 404:
            return None
        raise

    # Preserve order but drop repeats: one message can appear in several records.
    return list(dict.fromkeys(message_ids)), newest


def _from_recent_window(service, minutes: int = WINDOW_MINUTES) -> list[str]:
    """Fall back to listing Job Apps messages from the last N minutes.

    Used on the first ever run and whenever the stored cursor has expired.
    """
    listing = (
        service.users()
        .messages()
        .list(userId="me", labelIds=[settings.JOB_APPS_LABEL_ID], maxResults=SCAN_LIMIT)
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
            break  # Gmail returns newest first, so the rest are older too.
        recent.append(stub["id"])

    return recent


def messages_to_process(service) -> tuple[list[str], int | None]:
    """Return Job Apps message ids to handle now, plus the cursor value to
    store once they have all been processed successfully.

    The caller is responsible for advancing the cursor. Advancing it here
    would skip past messages whose processing later failed.
    """
    cursor = get_cursor()

    if cursor is not None:
        result = _from_history(service, cursor)
        if result is not None:
            return result
        print("cursor expired, falling back to recency window")

    message_ids = _from_recent_window(service)
    profile = service.users().getProfile(userId="me").execute()
    return message_ids, int(profile["historyId"])