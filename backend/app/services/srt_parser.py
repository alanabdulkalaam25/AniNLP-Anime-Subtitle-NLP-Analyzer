"""Parse SubRip (.srt) documents into structured subtitle entries."""

from __future__ import annotations

import re

from app.models.schemas import SubtitleEntry

_BLOCK_SEPARATOR = re.compile(r"\n\s*\n")
_MAX_SUBTITLE_ENTRIES = 2_000
_TIMECODE = re.compile(
    r"^(?P<start>\d{1,}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*"
    r"(?P<end>\d{1,}:\d{2}:\d{2}[,.]\d{1,3})(?:\s+.*)?$"
)


class SRTParseError(ValueError):
    """Raised when subtitle content cannot be interpreted as SubRip data."""


def _parse_timecode(raw: str) -> tuple[str, int]:
    """Parse timecode into a canonical HH:MM:SS,mmm string and total milliseconds."""
    cleaned = raw.replace(".", ",")
    time_part, ms_part = cleaned.split(",")
    h_str, m_str, s_str = time_part.split(":")
    h = int(h_str)
    m = int(m_str)
    s = int(s_str)
    ms = int(ms_part.ljust(3, "0")[:3])
    if m >= 60 or s >= 60:
        raise ValueError(f"Invalid minutes/seconds in timecode: {raw}")
    total_ms = ((h * 60 + m) * 60 + s) * 1000 + ms
    normalized = f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return normalized, total_ms


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
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        # Check if first line is a timecode (indexless SRT format)
        if _TIMECODE.match(lines[0]):
            timing_match = _TIMECODE.match(lines[0])
            source_index = block_number
            text_lines = lines[1:]
        else:
            if len(lines) < 3:
                raise SRTParseError(f"Subtitle block {block_number} is incomplete.")
            try:
                source_index = int(lines[0])
            except ValueError as error:
                raise SRTParseError(
                    f"Subtitle block {block_number} has an invalid cue index."
                ) from error

            if source_index < 1:
                raise SRTParseError(
                    f"Subtitle block {block_number} has cue index {source_index}; cue indexes must be >= 1."
                )

            timing_match = _TIMECODE.match(lines[1])
            if timing_match is None:
                raise SRTParseError(
                    f"Subtitle block {block_number} has an invalid timecode."
                )
            text_lines = lines[2:]

        if not text_lines:
            raise SRTParseError(f"Subtitle block {block_number} has no subtitle text.")

        try:
            start_str, start_ms = _parse_timecode(timing_match.group("start"))
            end_str, end_ms = _parse_timecode(timing_match.group("end"))
        except ValueError as error:
            raise SRTParseError(
                f"Subtitle block {block_number} has an invalid timecode: {error}"
            ) from error

        if end_ms < start_ms:
            raise SRTParseError(
                f"Subtitle block {block_number} has end timecode earlier than start timecode."
            )

        entries.append(
            SubtitleEntry(
                index=source_index,
                start=start_str,
                end=end_str,
                text=" ".join(text_lines),
            )
        )

    return entries
