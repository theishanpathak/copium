"""Logging that keeps email content out of public CI logs.

The repo is public, so the Actions tab is world-readable. Rejection text,
company names, and card copy must not appear there. Full inputs and outputs are
already captured in Langfuse, which is private, so nothing is lost by staying
quiet in CI.
"""

import os

# GitHub Actions sets CI=true. Anywhere else is treated as a local run.
LOCAL = not os.environ.get("CI")


def step(label: str, message: str = "") -> None:
    """Status line. Safe to print anywhere, so never include email content."""
    print(f"  [{label}] {message}".rstrip())


def detail(message: str) -> None:
    """Email or card content. Printed locally, suppressed in CI."""
    if LOCAL:
        print(f"    {message}")