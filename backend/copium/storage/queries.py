"""Database queries. Nothing outside this module touches the Supabase client."""

from supabase import Client, create_client

from copium.config.settings import settings

client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
SINGLE_USER = "00000000-0000-0000-0000-000000000000"


def get_cursor() -> int | None:
    """Return the last processed historyId, or None if never set."""
    response = (
        client.table("gmail_cursor")
        .select("history_id")
        .eq("user_id", SINGLE_USER)
        .execute()
    )
    return int(response.data[0]["history_id"]) if response.data else None


def set_cursor(history_id: int) -> None:
    """Store the last processed historyId, inserting or updating as needed."""
    client.table("gmail_cursor").upsert(
        {
            "user_id": SINGLE_USER,
            "history_id": history_id,
            "updated_at": "now()",
        }
    ).execute()

def claim_message(message_id: str) -> bool:
    """Try to claim a message for processing.
    Inserts a row keyed on the Gmail message id. A duplicate key means another
    run already claimed it, so this run should skip. Postgres arbitrates the
    race rather than application logic.
    Returns:
        True if this run claimed the message, False if it was already taken.
    """
    try:
        client.table("processed_messages").insert({"message_id": message_id}).execute()
        return True
    except Exception as exc:
        if "duplicate key" in str(exc) or "23505" in str(exc):
            return False
        raise

def release_message(message_id: str) -> None:
    """Delete a claim so a failed message can be retried on the next trigger."""
    client.table("processed_messages").delete().eq("message_id", message_id).execute()


def record_outcome(message_id: str, outcome: str, email: dict | None = None) -> None:
    """Attach the outcome and email details to an existing claim.

    Email details are stored for every message, not just rejections, so
    non-rejections can be listed and linked back to Gmail without opening
    the mailbox to identify them.
    """
    update = {"outcome": outcome}

    if email:
        update |= {
            "subject": email.get("subject"),
            "sender": email.get("sender"),
            "received_at": email.get("received_at"),
        }

    client.table("processed_messages").update(update).eq(
        "message_id", message_id
    ).execute()


def insert_rejection(state: dict) -> str | None:
    """Store a finished rejection card.

    Idempotent on message_id: if a row already exists the insert is skipped
    rather than raising, since a retried run may have gotten this far before.

    Returns:
        The new row's id, or None if a card already existed for this message.
    """
    row = {
        "message_id": state["message_id"],
        "company_name": state["company_name"],
        "role": state["role"],
        "roast": state["roast"],
        "roast_source_fact": state.get("roast_source_fact"),
        "what_they_do": state.get("what_they_do"),
        "notable_facts": state.get("notable_facts"),
        "received_at": state.get("received_at"),
        "rejection_quote": state.get("classification_reasoning"),
    }

    try:
        response = client.table("rejections").insert(row).execute()
        return response.data[0]["id"]
    except Exception as exc:
        if "duplicate key" in str(exc) or "23505" in str(exc):
            return None
        raise


def get_subscriptions() -> list[dict]:
    """Every device registered for push."""
    response = (
        client.table("push_subscriptions").select("endpoint, p256dh, auth").execute()
    )
    return response.data or []


def delete_subscription(endpoint: str) -> None:
    """Remove a subscription the push service has reported as gone."""
    client.table("push_subscriptions").delete().eq("endpoint", endpoint).execute()