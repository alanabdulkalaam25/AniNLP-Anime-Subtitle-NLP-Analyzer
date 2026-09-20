"""Tests for complete subtitle analysis orchestration."""

from app.services.analysis_pipeline import AnalysisPipeline, decode_subtitle_content


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


def test_decode_subtitle_content_accepts_utf8_bom_and_cp932() -> None:
    assert decode_subtitle_content("字幕".encode("utf-8-sig")) == "字幕"
    assert decode_subtitle_content("字幕".encode("cp932")) == "字幕"
