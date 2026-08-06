"""Pipeline entrypoint.

Reads message ids from the MESSAGE_IDS env var (set by the gate step in CI),
fetches each email, and runs it through the graph. Fetching happens here rather
than inside the graph so every node stays pure.
"""

import os
import sys

from copium.gmail_auth import get_gmail_service
from copium.graph import graph
from copium.fetch import fetch_email


def process(message_id: str, service) -> None:
    """Fetch one email and run it through the pipeline."""
    print(f"\n=== {message_id}")

    email = fetch_email(service, message_id)
    result = graph.invoke({"message_id": message_id, **email})

    if result.get("roast"):
        print(f"  CARD: {result['roast']}")
    else:
        print(f"  no card ({result.get('category')})")


def main() -> None:
    """Process every message id passed in MESSAGE_IDS."""
    message_ids = os.environ.get("MESSAGE_IDS", "").split()

    if not message_ids:
        print("no message ids given, nothing to do")
        return

    print(f"processing {len(message_ids)} message(s)")
    service = get_gmail_service()
    failures = 0

    for message_id in message_ids:
        try:
            process(message_id, service)
        except Exception as exc:
            failures += 1
            print(f"  FAILED {message_id}: {type(exc).__name__}: {exc}", file=sys.stderr)

    if failures:
        print(f"\n{failures} of {len(message_ids)} failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()