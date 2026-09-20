"""Tests for subtitle text preprocessing."""

from app.services.preprocessor import preprocess_text


def test_preprocess_text_removes_markup_and_preserves_japanese_punctuation() -> None:
    text = "<font color=\"white\">今日は  学校へ</font>\\N{\\an8}行きます。"

    assert preprocess_text(text) == "今日は 学校へ 行きます。"
