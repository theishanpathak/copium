"""Shared Gmail message parsing utilities."""

import base64
import html
import re
from typing import Any

HEADERS_WANTED = ("Subject", "From", "Date")

_BLOCK_TAGS_TO_DROP = re.compile(
    r"<(script|style|head)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE
)
_ANY_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")
_URL = re.compile(r"https?://\S+")


def decode_body(data: str) -> str:
    """Decode Gmail's base64url body data, tolerating stripped padding."""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def html_to_text(raw_html: str) -> str:
    """Convert an HTML email body to plain text.

    Drops <script>/<style>/<head> blocks (contents included, not just the
    tags), strips remaining tags, then delegates to _clean_text for entity
    unescaping and whitespace collapsing.
    """
    without_blocks = _BLOCK_TAGS_TO_DROP.sub(" ", raw_html)
    without_tags = _ANY_TAG.sub(" ", without_blocks)
    return _clean_text(without_tags)


def _readable_length(text: str) -> int:
    """Length of text ignoring URLs, as a proxy for how much it actually says.

    Used only for comparison. URLs stay in the returned body because some
    senders encode the outcome in a tracking parameter and nowhere else.
    """
    return len(_URL.sub(" ", text).strip())


def extract_body(payload: dict[str, Any]) -> str:
    """Walk a MIME tree for the best text body.

    Prefers text/plain, except when it says almost nothing. Senders like
    LinkedIn put only navigation and legal boilerplate in the plain-text part
    and the real message in HTML, so compare readable content and take whichever
    actually carries the email.
    """
    plain: list[str] = []
    html_parts: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            if mime == "text/plain":
                plain.append(decode_body(data))
            elif mime == "text/html":
                html_parts.append(decode_body(data))
        for sub in part.get("parts", []):
            walk(sub)

    walk(payload)

    plain_text = _clean_text("\n".join(plain)) if plain else ""
    html_text = html_to_text("\n".join(html_parts)) if html_parts else ""

    if _readable_length(html_text) > _readable_length(plain_text):
        return html_text
    return plain_text or html_text


def _clean_text(text: str) -> str:
    """Unescape HTML entities and collapse whitespace, regardless of source."""
    return _WHITESPACE.sub(" ", html.unescape(text)).strip()


def extract_headers(payload: dict[str, Any]) -> dict[str, str]:
    """Pull the headers we care about (Subject, From, Date) from a message payload."""
    return {
        h["name"]: h["value"]
        for h in payload.get("headers", [])
        if h["name"] in HEADERS_WANTED
    }