"""Pipeline entrypoint and orchestrator.

Reads message ids from the MESSAGE_IDS env var (set by the gate step in CI),
fetches each email, and runs it through the graph. Fetching happens here rather
than inside the graph so every node stays pure. All Langfuse setup lives here so
the nodes stay unaware of tracing.
"""

import os
import sys

from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

from copium.config.settings import settings
from copium.fetch import fetch_email
from copium.gmail_auth import get_gmail_service
from copium.graph import graph

Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,
)
langfuse = get_client()


def process(message_id: str, service, handler: CallbackHandler) -> str:
    """Fetch one email, run the graph, and report the outcome.

    Returns:
        "roasted" if a card was produced, otherwise the category that caused
        the early exit.
    """
    email = fetch_email(service, message_id)
    result = graph.invoke(
        {"message_id": message_id, **email},
        config={"callbacks": [handler], "run_name": f"copium-{message_id}"},
    )

    if result.get("roast"):
        print(f"  CARD: {result['roast']}")
        return "roasted"

    category = result.get("category", "unknown")
    print(f"  no card ({category})")
    return category


def main() -> None:
    """Process every message id passed in MESSAGE_IDS."""
    message_ids = os.environ.get("MESSAGE_IDS", "").split()

    if not message_ids:
        print("no message ids given, nothing to do")
        return

    print("\n" + "#" * 60)
    print(f"# COPIUM PIPELINE RUN — {len(message_ids)} message(s)")
    print("#" * 60)

    service = get_gmail_service()
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

    print("\n" + "#" * 60)
    print("# RUN COMPLETE")
    for outcome, count in sorted(outcomes.items()):
        print(f"#   {outcome}: {count}")
    print("#" * 60 + "\n")

    langfuse.flush()

    if outcomes.get("errored"):
        sys.exit(1)


if __name__ == "__main__":
    main()