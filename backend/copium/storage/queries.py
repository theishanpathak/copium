"""Database queries. Nothing outside this module touches the Supabase client."""

from supabase import Client, create_client

from copium.config.settings import settings

client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)

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


def record_outcome(message_id: str, outcome: str) -> None:
    """Attach the outcome to an existing claim."""
    client.table("processed_messages").update({"outcome": outcome}).eq(
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
    }

    try:
        response = client.table("rejections").insert(row).execute()
        return response.data[0]["id"]
    except Exception as exc:
        if "duplicate key" in str(exc) or "23505" in str(exc):
            return None
        raise