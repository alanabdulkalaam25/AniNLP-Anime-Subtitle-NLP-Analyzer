"""Parse SubRip (.srt) documents into structured subtitle entries."""

from __future__ import annotations

import re

from app.models.schemas import SubtitleEntry

_BLOCK_SEPARATOR = re.compile(r"\n\s*\n")
_MAX_SUBTITLE_ENTRIES = 2_000
_TIMECODE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2},\d{3})(?:\s+.*)?$"
)


class SRTParseError(ValueError):
    """Raised when subtitle content cannot be interpreted as SubRip data."""


def parse_srt(content: str) -> list[SubtitleEntry]:
    """Parse SRT text while preserving source timing and subtitle order.

    SRT text lines belonging to one cue are joined with a space. Cleaning markup
    and whitespace is deliberately deferred to the preprocessing service.
    """
    normalized_content = (
        content.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    )
    if not normalized_content:
        raise SRTParseError("Subtitle file is empty.")

    entries: list[SubtitleEntry] = []
    blocks = _BLOCK_SEPARATOR.split(normalized_content)
    if len(blocks) > _MAX_SUBTITLE_ENTRIES:
        raise SRTParseError(
            f"Subtitle file contains more than {_MAX_SUBTITLE_ENTRIES} cues."
        )

    for block_number, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.split("\n")]
        if len(lines) < 3:
            raise SRTParseError(f"Subtitle block {block_number} is incomplete.")

        try:
            source_index = int(lines[0])
        except ValueError as error:
            raise SRTParseError(
                f"Subtitle block {block_number} has an invalid cue index."
            ) from error

        timing = _TIMECODE.match(lines[1])
        if timing is None:
            raise SRTParseError(
                f"Subtitle block {block_number} has an invalid timecode."
            )

        text_lines = [line for line in lines[2:] if line]
        if not text_lines:
            raise SRTParseError(f"Subtitle block {block_number} has no subtitle text.")

        entries.append(
            SubtitleEntry(
                index=source_index,
                start=timing.group("start"),
                end=timing.group("end"),
                text=" ".join(text_lines),
            )
        )

    return entries
