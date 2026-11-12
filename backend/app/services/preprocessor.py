"""Conservative cleanup for subtitle text before NLP processing."""

from __future__ import annotations

import html
import re

_ASS_TAG = re.compile(r"(?:\\N)?\{\\[^}]*\}")
_ASS_LINE_BREAK = re.compile(r"\\[Nnh]")
_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    """Remove presentation markup without removing Japanese linguistic content."""
    cleaned = html.unescape(text)
    cleaned = cleaned.replace("\ufeff", "").replace("\u200b", "")
    cleaned = _ASS_TAG.sub(" ", cleaned)
    cleaned = _ASS_LINE_BREAK.sub(" ", cleaned)
    cleaned = _HTML_TAG.sub("", cleaned)
    return _WHITESPACE.sub(" ", cleaned).strip()
