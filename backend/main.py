"""Pipeline entrypoint and orchestrator.

Resolves which messages to process, runs each through the graph, and only
advances the Gmail cursor once the whole batch has succeeded. Fetching happens
here rather than inside the graph so every node stays pure.
"""

import os
import sys

from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

from copium.config.settings import settings
from copium.fetch import fetch_email
from copium.gate import messages_to_process
from copium.gmail_auth import get_gmail_service
from copium.graph import graph
from copium.storage.queries import (
    claim_message,
    insert_rejection,
    record_outcome,
    release_message,
    set_cursor,
)

Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,
)
langfuse = get_client()


def process(message_id: str, service, handler: CallbackHandler) -> str:
    """Fetch one email, run the graph, store the result.

    Claims the message first so concurrent runs skip instead of paying for the
    pipeline again. Releases the claim on failure so it can be retried.
    """
    if not claim_message(message_id):
        print("  already processed, skipping")
        return "skipped"

    try:
        email = fetch_email(service, message_id)
        result = graph.invoke(
            {"message_id": message_id, **email},
            config={"callbacks": [handler], "run_name": f"copium-{message_id}"},
        )
    except Exception:
        release_message(message_id)
        raise

    if result.get("roast"):
        rejection_id = insert_rejection(result)
        print(f"  CARD: {result['roast']}")
        print(f"  stored: {rejection_id or 'already existed'}")
        outcome = "roasted"
    else:
        outcome = result.get("category", "unknown")
        print(f"  no card ({outcome})")

    record_outcome(message_id, outcome)
    return outcome


def main() -> None:
    """Resolve messages, process them, advance the cursor if all succeeded."""
    service = get_gmail_service()

    override = os.environ.get("MESSAGE_IDS", "").split()
    if override:
        message_ids, new_cursor = override, None
        print(f"MESSAGE_IDS override: {len(message_ids)} message(s)")
    else:
        message_ids, new_cursor = messages_to_process(service)

    if not message_ids:
        print("nothing to process")
        if new_cursor is not None:
            set_cursor(new_cursor)
        return

    print("\n" + "#" * 60)
    print(f"# COPIUM PIPELINE RUN — {len(message_ids)} message(s)")
    print("#" * 60)

    handler = CallbackHandler()
    outcomes: dict[str, int] = {}

    for message_id in message_ids:
        print(f"\n--- {message_id}")
        try:
            outcome = process(message_id, service, handler)
        except Exception as exc:
            outcome = "errored"
            print(f"  FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)

        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    failed = outcomes.get("errored", 0)

    # Only advance past messages we actually handled. Leaving the cursor put
    # means the next run re-offers the whole batch; claim_message no-ops the
    # ones that already succeeded, so only the failure is retried.
    if new_cursor is not None and not failed:
        set_cursor(new_cursor)
        print(f"\ncursor advanced to {new_cursor}")
    elif failed:
        print("\ncursor held back for retry", file=sys.stderr)

    print("\n" + "#" * 60)
    print("# RUN COMPLETE")
    for outcome, count in sorted(outcomes.items()):
        print(f"#   {outcome}: {count}")
    print("#" * 60 + "\n")

    langfuse.flush()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()