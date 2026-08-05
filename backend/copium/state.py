"""Shared state for the Copium pipeline graph."""

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["rejection", "advancement", "acknowledgment", "offer", "other"]


class PipelineState(BaseModel):
    """State threaded through every node in the graph."""

    # Entry point — supplied by the caller.
    message_id: str
    history_id: str | None = None

    # Written by: fetch/parse
    subject: str | None = None
    sender: str | None = None
    received_at: str | None = None
    body: str | None = None

    # Written by: classify (Phase 5)
    category: Category | None = None
    is_rejection: bool | None = None
    classification_reasoning: str | None = None

    # Written by: extract (Phase 6)
    company_name: str | None = None
    role: str | None = None

    # Written by: research (Phase 7)
    research_notes: str | None = None

    # Written by: roast (Phase 8)
    roast: str | None = None

    # Written by: render (Phase 11)
    card_url: str | None = None