"""Conservative cleanup for subtitle text before NLP processing."""

from __future__ import annotations

import html
import re

_ASS_TAG = re.compile(r"(?:\\N)?\{\\[^}]*\}")
_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    """Remove presentation markup without removing Japanese linguistic content."""
    cleaned = html.unescape(text)
    cleaned = _ASS_TAG.sub(" ", cleaned)
    cleaned = _HTML_TAG.sub("", cleaned)
    return _WHITESPACE.sub(" ", cleaned).strip()
