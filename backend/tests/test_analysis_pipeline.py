"""Tests for complete subtitle analysis orchestration."""

import pytest

from app.services.analysis_pipeline import (
    AnalysisPipeline,
    AnalysisTimeoutError,
    decode_subtitle_content,
)


def test_pipeline_analyzes_sample_subtitles() -> None:
    result = AnalysisPipeline().analyze(
        "1\n00:00:01,000 --> 00:00:03,000\n今日は学校へ行きます。",
        "lesson.srt",
    )

    assert result.subtitle.filename == "lesson.srt"
    assert result.subtitle.subtitle_count == 1
    assert result.statistics.total_sentences == 1
    assert result.statistics.total_tokens == 7
    assert result.jlpt_distribution["N5"] == 3
    assert result.sentences[0].tokens[4].base == "行く"
    assert {word.word for word in result.top_words} >= {"今日", "学校", "行く"}


def test_pipeline_skips_empty_cues() -> None:
    result = AnalysisPipeline().analyze(
        "1\n00:00:01,000 --> 00:00:02,000\n<i></i>\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nこんにちは",
        "empty_cues.srt",
    )

    # Empty cue is filtered out
    assert result.subtitle.subtitle_count == 1
    assert result.statistics.total_sentences == 1
    assert len(result.sentences) == 1
    assert result.sentences[0].text == "こんにちは"


def test_pipeline_respects_deadline() -> None:
    pipeline = AnalysisPipeline()
    with pytest.raises(AnalysisTimeoutError):
        pipeline.analyze(
            "1\n00:00:01,000 --> 00:00:03,000\n今日は学校へ行きます。",
            "timeout.srt",
            deadline=0.0,  # Expired deadline
        )


def test_decode_subtitle_content_accepts_utf8_bom_cp932_and_utf16() -> None:
    assert decode_subtitle_content("字幕".encode("utf-8-sig")) == "字幕"
    assert decode_subtitle_content("字幕".encode("cp932")) == "字幕"
    assert decode_subtitle_content("字幕".encode("utf-16")) == "字幕"
