"""Tests for SubRip parsing."""

import pytest

from app.services.srt_parser import SRTParseError, parse_srt


def test_parse_srt_returns_entries_with_timing_and_joined_text() -> None:
    entries = parse_srt(
        "1\n00:00:01,000 --> 00:00:03,000\n今日はいい天気ですね。\n\n"
        "2\n00:00:04,000 --> 00:00:06,000\n学校へ\n行きましょう。"
    )

    assert len(entries) == 2
    assert entries[0].model_dump() == {
        "index": 1,
        "start": "00:00:01,000",
        "end": "00:00:03,000",
        "text": "今日はいい天気ですね。",
    }
    assert entries[1].text == "学校へ 行きましょう。"


@pytest.mark.parametrize("content", ["", "1\ninvalid\ntext", "one\n00:00:01,000 --> 00:00:03,000\ntext", "0\n00:00:01,000 --> 00:00:03,000\ntext", "-1\n00:00:01,000 --> 00:00:03,000\ntext"])
def test_parse_srt_rejects_empty_or_malformed_documents(content: str) -> None:
    with pytest.raises(SRTParseError):
        parse_srt(content)


def test_parse_srt_handles_period_ms_and_single_digit_hours() -> None:
    entries = parse_srt("1\n0:00:01.500 --> 0:00:03.000\nテスト")
    assert len(entries) == 1
    assert entries[0].start == "00:00:01,500"
    assert entries[0].end == "00:00:03,000"


def test_parse_srt_supports_indexless_cues() -> None:
    entries = parse_srt("00:00:01,000 --> 00:00:02,000\nIndexless cue")
    assert len(entries) == 1
    assert entries[0].index == 1
    assert entries[0].text == "Indexless cue"


def test_parse_srt_rejects_end_before_start() -> None:
    with pytest.raises(SRTParseError, match="earlier than start"):
        parse_srt("1\n00:00:05,000 --> 00:00:02,000\nInvalid timing")
